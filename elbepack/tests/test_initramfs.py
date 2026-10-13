# ELBE - Debian Based Embedded Rootfilesystem Builder
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 KUKA Deutschland GmbH

import contextlib
import os
import re
import shutil
import subprocess

import pytest

from elbepack import initramfs


pytestmark = pytest.mark.skipif(os.geteuid() != 0, reason='requires execution as root')


@pytest.fixture
def root(tmp_path):
    for directory in ('usr/bin', 'usr/sbin', 'var/lib/dpkg'):
        (tmp_path / directory).mkdir(parents=True)
    (tmp_path / 'var/lib/dpkg/status').touch()

    for executable in ('/bin/sh', '/usr/bin/dpkg-divert'):
        dependencies = subprocess.run(
            ['ldd', executable], check=True, capture_output=True, text=True,
        )
        for source in (executable, *re.findall(r'/\S+', dependencies.stdout)):
            destination = tmp_path / source.lstrip('/')
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    return tmp_path


def assert_restored(root):
    result = subprocess.run(
        ['/usr/sbin/chroot', str(root), 'dpkg-divert', '--list'],
        check=True, capture_output=True, text=True,
    )
    assert result.stdout == ''
    assert not list(root.rglob('*.elbe-distrib'))


@pytest.mark.parametrize('existing', (False, True))
@pytest.mark.parametrize('fail', (False, True))
def test_restores_tools(root, existing, fail):
    for tool in initramfs.INITRAMFS_TOOLS:
        if existing:
            path = root / tool.lstrip('/')
            path.write_text('original')
            path.chmod(0o750)

    expected_error = (
        pytest.raises(RuntimeError, match='installation failed')
        if fail else contextlib.nullcontext()
    )
    with expected_error:
        with initramfs.disable_initramfs_generation(str(root)):
            for tool in initramfs.INITRAMFS_TOOLS:
                path = root / tool.lstrip('/')
                result = subprocess.run(
                    ['/usr/sbin/chroot', str(root), tool],
                    capture_output=True, text=True, check=True,
                )
                assert 'skipping automatic initramfs generation' in result.stderr
                path.with_name(path.name + '.elbe-distrib').write_text('installed')
            if fail:
                raise RuntimeError('installation failed')

    assert_restored(root)
    for tool in initramfs.INITRAMFS_TOOLS:
        assert (root / tool.lstrip('/')).read_text() == 'installed'


def test_no_package_installed(root):
    with initramfs.disable_initramfs_generation(str(root)):
        pass
    assert_restored(root)
    for tool in initramfs.INITRAMFS_TOOLS:
        assert not (root / tool.lstrip('/')).exists()


@pytest.mark.parametrize('tool', initramfs.INITRAMFS_TOOLS)
def test_preserves_existing_diversion(root, tool):
    subprocess.run(
        ['/usr/sbin/chroot', str(root), 'dpkg-divert', '--local', '--add', '--rename',
         '--divert', tool + '.custom', tool],
        check=True,
    )
    with pytest.raises(RuntimeError, match='existing diversion'):
        with initramfs.disable_initramfs_generation(str(root)):
            pytest.fail('must not install over an existing diversion')
    for entrypoint in initramfs.INITRAMFS_TOOLS:
        assert not (root / entrypoint.lstrip('/')).exists()
    result = subprocess.run(
        ['/usr/sbin/chroot', str(root), 'dpkg-divert', '--list'],
        check=True, capture_output=True, text=True,
    )
    assert '.custom' in result.stdout
    assert '.elbe-distrib' not in result.stdout


@pytest.mark.parametrize('tool', ('/usr/sbin/mkinitramfs', '/usr/sbin/mktirfs'))
def test_preserves_low_level_generators(root, tool):
    path = root / tool.lstrip('/')
    path.write_text('#!/bin/sh\necho "low-level generator"\n')
    path.chmod(0o750)

    with initramfs.disable_initramfs_generation(str(root)):
        result = subprocess.run(
            ['/usr/sbin/chroot', str(root), tool],
            check=True, capture_output=True, text=True,
        )
        assert result.stdout == 'low-level generator\n'
        assert path.stat().st_mode & 0o777 == 0o750

    assert_restored(root)
    assert path.read_text() == '#!/bin/sh\necho "low-level generator"\n'
    assert path.stat().st_mode & 0o777 == 0o750
