// Copyright Epic Games, Inc. All Rights Reserved.

#include "tpUnreal.h"

#define LOCTEXT_NAMESPACE "FtpUnrealModule"

void FtpUnrealModule::StartupModule()
{
	UE_LOG(LogTemp, Warning, TEXT("Hello from tpUnreal!"));
}

void FtpUnrealModule::ShutdownModule()
{
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FtpUnrealModule, tpUnreal)