#pragma once

#include "Modules/ModuleManager.h"

DECLARE_LOG_CATEGORY_EXTERN(LogTpLevelSelector, Log, All);

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
