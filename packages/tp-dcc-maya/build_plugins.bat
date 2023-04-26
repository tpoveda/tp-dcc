mkdir build
cmake -H. -Bbuild -G "Visual Studio 16 2019"
cmake --build build/
cmake --build build/ --con