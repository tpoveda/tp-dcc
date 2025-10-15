#include "tpAdvancedDeletionStyle.h"

#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyleRegistry.h"

FName FtpAdvancedDeletionStyle::StyleSetName = FName("tpAdvancedDeletionStyle");
TSharedPtr<FSlateStyleSet> FtpAdvancedDeletionStyle::StyleSet = nullptr;

void FtpAdvancedDeletionStyle::Initialize()
{
	if (!StyleSet.IsValid())
	{
		StyleSet = CreateSlateStyleSet();
		FSlateStyleRegistry::RegisterSlateStyle(*StyleSet);
	}
}

void FtpAdvancedDeletionStyle::Shutdown()
{
	if (StyleSet.IsValid())
	{
		FSlateStyleRegistry::UnRegisterSlateStyle(*StyleSet);
		StyleSet.Reset();
	}
}

FName FtpAdvancedDeletionStyle::GetStyleSetName()
{
	return StyleSetName;
}

TSharedRef<FSlateStyleSet> FtpAdvancedDeletionStyle::CreateSlateStyleSet()
{
	TSharedRef<FSlateStyleSet> CustomStyleSet =  MakeShareable(new FSlateStyleSet(StyleSetName));

	const FString ResourcesDirectory = IPluginManager::Get().FindPlugin("tpAdvancedDeletion")->GetBaseDir() / "Resources";
	CustomStyleSet->SetContentRoot(ResourcesDirectory);

	const FVector2D Icon16X16(16.0f, 16.0f);
	CustomStyleSet->Set("tpAdvancedDeletion.DeleteEmptyFolders", new FSlateImageBrush(ResourcesDirectory / "DeleteEmptyFolders.png", Icon16X16));
	CustomStyleSet->Set("tpAdvancedDeletion.DeleteUnusedAssets", new FSlateImageBrush(ResourcesDirectory / "DeleteUnusedAssets.png", Icon16X16));
	CustomStyleSet->Set("tpAdvancedDeletion.AdvancedDeletion", new FSlateImageBrush(ResourcesDirectory / "AdvancedDeletion.png", Icon16X16));

	return CustomStyleSet;
}
