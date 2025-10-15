#include "tpLevelSelectorStyle.h"

#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyleRegistry.h"

FName FtpLevelSelectorStyle::StyleSetName = FName("tpLevelSelectorStyle");
TSharedPtr<FSlateStyleSet> FtpLevelSelectorStyle::StyleSet = nullptr;

void FtpLevelSelectorStyle::Initialize()
{
	if (!StyleSet.IsValid())
	{
		StyleSet = CreateSlateStyleSet();
		FSlateStyleRegistry::RegisterSlateStyle(*StyleSet);
	}
}

void FtpLevelSelectorStyle::Shutdown()
{
	if (StyleSet.IsValid())
	{
		FSlateStyleRegistry::UnRegisterSlateStyle(*StyleSet);
		StyleSet.Reset();
	}
}

FName FtpLevelSelectorStyle::GetStyleSetName()
{
	return StyleSetName;
}

const ISlateStyle& FtpLevelSelectorStyle::Get()
{
	return *StyleSet;
}

TSharedRef<FSlateStyleSet> FtpLevelSelectorStyle::CreateSlateStyleSet()
{
	TSharedRef<FSlateStyleSet> CustomStyleSet =  MakeShareable(new FSlateStyleSet(StyleSetName));

	const FString ResourcesDirectory = IPluginManager::Get().FindPlugin("tpLevelSelector")->GetBaseDir() / "Resources";
	CustomStyleSet->SetContentRoot(ResourcesDirectory);

	const FVector2D Icon16X16(16.0f, 16.0f);
	CustomStyleSet->Set("tpLevelSelector.Refresh", new FSlateImageBrush(ResourcesDirectory / "Refresh.png", Icon16X16));

	return CustomStyleSet;
}
