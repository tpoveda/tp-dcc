// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Modules/ModuleManager.h"

class StpLevelSelectorWidget;
class FExtender;
class FToolBarBuilder;

class FtpLevelSelectorModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
	void AddToolbarExtension(FToolBarBuilder& Builder);
	TSharedPtr<FExtender> ToolbarExtender;
	TSharedPtr<StpLevelSelectorWidget> LevelSelectorWidget;
};
