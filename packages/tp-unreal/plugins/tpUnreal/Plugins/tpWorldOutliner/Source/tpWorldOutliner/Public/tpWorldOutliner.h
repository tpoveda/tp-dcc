// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Modules/ModuleManager.h"

class AActor;
class FUICommandList;
class FExtender;
class FMenuBuilder;

class FtpWorldOutlinerModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
	void InitializeLevelEditorExtension();

	TSharedRef<FExtender> CustomLevelEditorMenuExtender(const TSharedRef<FUICommandList> UICommandList, const TArray<AActor*> SelectedActors);
	void AddLevelEditorMenuEntry(FMenuBuilder& MenuBuilder);
	void OnLockActorSelectionButtonClicked();
	void OnUnlockActorSelectionButtonClicked();

	void InitializeCustomSelectionEvent();
	void OnActorSelected(UObject* SelectedObject);
};
