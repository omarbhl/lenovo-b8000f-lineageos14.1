# Build host dependencies

Use **64-bit Ubuntu 20.04**, native Linux or WSL2, matching the development host.
Build in the Linux filesystem (for example `$HOME/b8000-build`) rather than under
`/mnt/c` or `/mnt/e`: Android creates many files and relies on Unix modes/symlinks.
Allow roughly 15 GB free for the minimal checkout, build outputs and image inputs,
and more for caches. The development build used 4 build jobs and 8 GB available RAM.

The legacy source requires **OpenJDK8** and **Python2**. Python3 drives this
repository's image scripts and the current Google repo launcher. Do not replace
the system `python` or `java` globally: build_components.sh creates a private
Python2 command shim and uses JAVA_HOME only for its process.

On Ubuntu20.04:

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends \
  ca-certificates git curl python2 python3 openjdk-8-jdk-headless \
  build-essential gcc-multilib g++-multilib bc bison flex zip unzip rsync \
  ccache libncurses5 libncurses5-dev lib32z1-dev zlib1g-dev libssl-dev \
  libxml2-utils xsltproc lzop liblz4-tool xz-utils patch file cpio \
  e2fsprogs gzip openssl coreutils
```

Package names above are for20.04. If a newer distribution lacks Python2, Java8
or old prebuilt-library compatibility, use a dedicated20.04 build environment;
do not silently substitute newer tools and assume the output is equivalent.
The compiler/sysroot come from the pinned Android checkout, not the host GCC:
ARM32 `arm-linux-androideabi-4.9` and `prebuilts/ndk/current/platforms/android-21`.

Install Google's `repo` launcher following the [official instructions](https://source.android.com/docs/setup/download#installing-repo).
For a user-local launcher installation:

```sh
mkdir -p "$HOME/.local/bin"
curl --fail --location https://storage.googleapis.com/git-repo-downloads/repo \
  -o "$HOME/.local/bin/repo"
chmod 0755 "$HOME/.local/bin/repo"
export PATH="$HOME/.local/bin:$PATH"
repo version
```

The launcher bootstraps upstream repo. Its downloads are external tool dependencies;
review and record its version for your build rather than committing credentials
or caches. The Android component commits themselves are pinned in the repository.

Check tools before building:

```sh
python2 --version
python3 --version
JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
"$JAVA_HOME/bin/java" -version
debugfs -V
resize2fs -V 2>&1 | head -1
git --version
gzip --version | head -1
```

Python image tools use the standard library; no pip packages are required. GNU
gzip at compression level9 is used by the exact-size kernel patching procedure. Do not replace
that step with Python's compressor without its size and roundtrip checks.

This workflow does not need ADB, a connected tablet, root access to a tablet,
the maintainer's private signing keys, account data, NVRAM or calibration images. It does require
locally supplied verified firmware inputs described in [SOURCES.md](SOURCES.md).
