// Copyright Epic Games, Inc. All Rights Reserved.

#include "tpWorldOutliner.h"

#include "LevelEditor.h"
#include "Selection.h"

#define LOCTEXT_NAMESPACE "FtpWorldOutlinerModule"

void FtpWorldOutlinerModule::StartupModule()
{
	InitializeLevelEditorExtension();
	InitializeCustomSelectionEvent();
}

void FtpWorldOutlinerModule::ShutdownModule()
{
}

void FtpWorldOutlinerModule::InitializeLevelEditorExtension()
{
	FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");

	TArray<FLevelEditorModule::FLevelViewportMenuExtender_SelectedActors>& LevelEditorMenuExtenders = LevelEditorModule.GetAllLevelViewportContextMenuExtenders();
	LevelEditorMenuExtenders.Add(FLevelEditorModule::FLevelViewportMenuExtender_SelectedActors::CreateRaw(this, &FtpWorldOutlinerModule::CustomLevelEditorMenuExtender));
}

TSharedRef<FExtender> FtpWorldOutlinerModule::CustomLevelEditorMenuExtender(
	const TSharedRef<FUICommandList> UICommandList, const TArray<AActor*> SelectedActors)
{
	TSharedRef<FExtender> MenuExtender = MakeShareable(new FExtender());

	if (SelectedActors.Num() > 0)
	{
		MenuExtender->AddMenuExtension(
			FName("ActorOptions"),
			EExtensionHook::Before,
			UICommandList,
			FMenuExtensionDelegate::CreateRaw(this, &FtpWorldOutlinerModule::AddLevelEditorMenuEntry));
	}
	
	return MenuExtender;
}

void FtpWorldOutlinerModule::AddLevelEditorMenuEntry(FMenuBuilder& MenuBuilder)
{
	MenuBuilder.AddMenuEntry(
		FText::FromString(TEXT("Lock Actor Selection")),
		FText::FromString(TEXT("Prevent actor from being selected")),
		FSlateIcon(),
		FExecuteAction::CreateRaw(this, &FtpWorldOutlinerModule::OnLockActorSelectionButtonClicked)
	);

	MenuBuilder.AddMenuEntry(
		FText::FromString(TEXT("Unlock All Actor Selection")),
		FText::FromString(TEXT("Remove the selection constraint on all actors")),
		FSlateIcon(),
		FExecuteAction::CreateRaw(this, &FtpWorldOutlinerModule::OnUnlockActorSelectionButtonClicked)
	);
}

void FtpWorldOutlinerModule::OnLockActorSelectionButtonClicked()
{
	GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::Cyan, TEXT("Locked"));
}

void FtpWorldOutlinerModule::OnUnlockActorSelectionButtonClicked()
{
	GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::Red, TEXT("Unlocked"));
}

void FtpWorldOutlinerModule::InitializeCustomSelectionEvent()
{
	USelection* UserSelection = GEditor->GetSelectedActors();
	UserSelection->SelectObjectEvent.AddRaw(this, &FtpWorldOutlinerModule::OnActorSelected);
}

void FtpWorldOutlinerModule::OnActorSelected(UObject* SelectedObject)
{
	if (!SelectedObject) return;
	if (AActor* SelectedActor = Cast<AActor>(SelectedObject))
	{
		GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::Cyan, SelectedActor->GetActorLabel());
	}
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FtpWorldOutlinerModule, tpWorldOutliner)