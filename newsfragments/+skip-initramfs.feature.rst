Add the opt-in target setting ``skip-initramfs`` to suppress automatic
initramfs generation by initramfs-tools, dracut, and tiny-initramfs only
during package installation. Suppress their installation entry points
``update-initramfs``, ``dracut``, and ``update-tirfs``, leaving direct calls
to low-level generators such as ``mkinitramfs`` and ``mktirfs`` unaffected.
Restore the original tools before finetuning, including when package
installation fails.
