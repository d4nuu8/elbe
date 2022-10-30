# Btrfs Subvolume Layouts

See [Btrfs SysadminGuide](https://btrfs.wiki.kernel.org/index.php/SysadminGuide#Layout)

## Nested

Example subvolume Layout:

```plain
toplevel                  (volume root directory, to be mounted at /)
+-- home                  (subvolume root directory)
+-- var                   (subvolume root directory)
    +-- www               (subvolume root directory)
    +-- lib               (directory)
         \-- postgresql   (subvolume root directory)
```

ELBE definition:

```xml
<fstab>
    <bylabel>
        <label>rfs</label>
        <mountpoint>/</mountpoint>
        <fs>
            <type>btrfs</type>
            <subvolumes>
                <subvolume>
                    <name>home</name>
                </subvolume>
                <subvolume>
                    <name>var</name>
                </subvolume>
                <subvolume>
                    <name>var/www</name>
                </subvolume>
                <subvolume>
                    <name>var/lib/postgresql</name>
                </subvolume>
            </subvolumes>
        </fs>
    </bylabel>
</fstab>
```

## Flat

Example subvolume Layout:

```plain
toplevel         (volume root directory, not to be mounted by default)
  +-- root       (subvolume root directory, to be mounted at /)
  +-- home       (subvolume root directory, to be mounted at /home)
  +-- var        (directory)
  |   \-- www    (subvolume root directory, to be mounted at /var/www)
  \-- postgres   (subvolume root directory, to be mounted at /var/lib/postgresql)
```

ELBE definition:

```xml
<fstab>
    <bylabel>
        <label>rfs</label>
        <mountpoint>/var/lib/btrfs</mountpoint>
        <fs>
            <type>btrfs</type>
            <subvolumes>
                <subvolume>
                    <name>root</name>
                    <mountpoint>/</mountpoint>
                </subvolume>
                <subvolume>
                    <name>home</name>
                    <mountpoint>/home</mountpoint>
                </subvolume>
                <subvolume>
                    <name>var/www</name>
                    <mountpoint>/var/www</mountpoint>
                </subvolume>
                <subvolume>
                    <name>postgres</name>
                    <mountpoint>/var/lib/postgresql</mountpoint>
                </subvolume>
            </subvolumes>
        </fs>
    </bylabel>
</fstab>
```
