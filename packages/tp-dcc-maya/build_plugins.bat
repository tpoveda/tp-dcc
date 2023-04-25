@echo off

if not exist build (mkdir build)
pushd build

if not exist win64 (mkdir win64)

pushd win64
echo "==> Creating Plugins win64 project"
cmake -DCMAKE_CONFIGURATION_TYPES="Debug;Release" -G "Visual Studio 16 2019" "%~dp0"
echo "==> Creating Plugins win64 project"
popd
popd


echo "================> Build process completed successfully!"