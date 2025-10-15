#include "tpLevelSelector.h"

#include "LevelEditor.h"
#include "STpLevelSelectorWidget.h"
#include "tpLevelSelectorStyle.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Framework/MultiBox/MultiBoxExtender.h"

DEFINE_LOG_CATEGORY(LogTpLevelSelector);

#define LOCTEXT_NAMESPACE "FtpLevelSelectorModule"


void FtpLevelSelectorModule::StartupModule()
{
	if (IsRunningCommandlet()) return;

	FtpLevelSelectorStyle::Initialize();

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

void FtpLevelSelectorModule::ShutdownModule()
{
		if (!FModuleManager::Get().IsModuleLoaded("LevelEditor")) return;

	if (ToolbarExtender.IsValid())
	{
		FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
		LevelEditorModule.GetToolBarExtensibilityManager()->RemoveExtender(ToolbarExtender);
		ToolbarExtender.Reset();
	}

	FtpLevelSelectorStyle::Shutdown();
}

void FtpLevelSelectorModule::AddToolbarExtension(FToolBarBuilder& Builder)
{
	Builder.AddWidget(SAssignNew(LevelSelectorWidget, StpLevelSelectorWidget));
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FtpLevelSelectorModule, tpLevelSelector)