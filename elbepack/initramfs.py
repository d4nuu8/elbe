# ELBE - Debian Based Embedded Rootfilesystem Builder
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 KUKA Deutschland GmbH

import contextlib
import pathlib
import subprocess
from collections.abc import Iterator

from elbepack.shellhelper import chroot


INITRAMFS_TOOLS = ('/usr/sbin/update-initramfs', '/usr/bin/dracut', '/usr/sbin/update-tirfs')


@contextlib.contextmanager
def disable_initramfs_generation(root: str) -> Iterator[None]:
    def restore(tool: str, diverted: str) -> None:
        pathlib.Path(root, tool.lstrip('/')).unlink(missing_ok=True)
        chroot(root, ['dpkg-divert', '--local', '--rename', '--remove',
                      '--divert', diverted, tool])

    with contextlib.ExitStack() as cleanup:
        for tool in INITRAMFS_TOOLS:
            diversion = subprocess.run(
                ['/usr/sbin/chroot', root, 'dpkg-divert', '--list', tool],
                check=True, capture_output=True, text=True,
            )
            if diversion.stdout:
                raise RuntimeError(f'Cannot suppress {tool}: an existing diversion is present')
            diverted = tool + '.elbe-distrib'
            chroot(root, ['dpkg-divert', '--local', '--rename', '--add',
                          '--divert', diverted, tool])
            cleanup.callback(restore, tool, diverted)
            path = pathlib.Path(root, tool.lstrip('/'))
            path.write_text(
                '#!/bin/sh\n'
                'echo "ELBE: skipping automatic initramfs generation" >&2\n'
                'exit 0\n',
            )
            path.chmod(0o755)
        yield
