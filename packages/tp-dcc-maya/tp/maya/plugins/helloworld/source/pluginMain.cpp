#include <iostream>

#include <maya/MSimple.h>

DeclareSimpleCommand(HelloWorld, "Tomas Poveda", "Any");

MStatus HelloWorld::doIt(const MArgList&)
{
	std::cout << "Hello World\n" << std::endl;
	return MS::kSuccess;
}