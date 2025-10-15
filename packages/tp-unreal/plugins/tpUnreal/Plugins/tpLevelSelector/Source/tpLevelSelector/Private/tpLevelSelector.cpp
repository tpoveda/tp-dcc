// Copyright Epic Games, Inc. All Rights Reserved.

#include "tpLevelSelector.h"

#include "LevelEditor.h"
#include "STpLevelSelectorWidget.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Framework/MultiBox/MultiBoxExtender.h"

#define LOCTEXT_NAMESPACE "FtpLevelSelectorModule"

void FtpLevelSelectorModule::StartupModule()
{
	{
		if (IsRunningCommandlet()) return;
	
		ToolbarExtender = MakeShareable(new FExtender);
		ToolbarExtender->AddToolBarExtension(
			"Play",
			EExtensionHook::After,
			nullptr,
			FToolBarExtensionDelegate::CreateRaw(
				this,
				&FtpLevelSelectorModule::AddToolbarExtension
			)
		);

		FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
		LevelEditorModule.GetToolBarExtensibilityManager()->AddExtender(ToolbarExtender);
	}
}

void FtpLevelSelectorModule::ShutdownModule()
{
		if (!ToolbarExtender.IsValid()) return;
		if (!FModuleManager::Get().IsModuleLoaded("LevelEditor")) return;

		FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
		LevelEditorModule.GetToolBarExtensibilityManager()->RemoveExtender(ToolbarExtender);
		ToolbarExtender.Reset();
}

void FtpLevelSelectorModule::AddToolbarExtension(FToolBarBuilder& Builder)
{
	Builder.AddWidget(SAssignNew(LevelSelectorWidget, StpLevelSelectorWidget));
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FtpLevelSelectorModule, tpLevelSelector)