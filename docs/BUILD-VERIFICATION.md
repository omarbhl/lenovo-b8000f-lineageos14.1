# Contributor workflow verification

The portable workflow was exercised locally on Ubuntu20.04 under WSL2 with
Java8, Python2/3, the recorded Android checkout and the locked external inputs.
No connected tablet was flashed or read by these build scripts.

Completed stages:

- Original donor ZIP reconstruction from system.new.dat/transfer list.
- Offline donor resize to 1GiB, post-resize repair and read-only filesystem check.
- Extraction and SHA256 verification of 64 explicitly locked overlay files.
- Source compilation of init, installd, signapk and both HAL wrappers using the
  pinned checkout and checked-in patches/device configuration.
- SHA256 verification of cached copies of the three pinned application APKs.
- Assembly with every modified system file read back and hashed.
- Reconstruction of the exact reviewed Binder kernel payload and normal boot packing.
- Signing with a newly generated local test identity, not the maintainer's key.
- Successful final assembly exit, signature verification, ZIP CRC/payload checks
  and 80 independent boot/package/installer/public-default checks.
- The camera/sensor/app/installd overlay hashes match the recorded v0.2 fix inventory
  for every entry except the intentionally changed contributor build.prop metadata.

The generated signed test ZIP SHA256 was:

`156b85c5f5b64f4347cdc58368965c092645dc4f9d3c4b17214421091ab17a5a`

That test output and its key remain local and are not release assets. A new build
is not expected to have the same ZIP checksum. Reuse of the verified prepared
firmware and freshly source-built components was used for final assembly; stages
were exercised individually, not through a second network download of every input.

Shell/Python entry points were syntax-checked. The source-fetch helper uses the
commit-pinned manifest; its fresh full network synchronization was not repeated
in this verification. Component compilation used the existing pinned checkout.
An independent machine should still exercise the documented first-time checkout
and dependency installation before claiming universal build-host compatibility.

No runtime or recovery-install result is asserted for the contributor-generated
ZIP. Hardware confirmation applies to the earlier development fixes. Perform the
manual test checklist on each newly generated package and signing identity.
