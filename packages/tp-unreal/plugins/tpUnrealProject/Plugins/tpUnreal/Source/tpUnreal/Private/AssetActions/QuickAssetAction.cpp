#include "DebugHelpers.h"
#include "AssetActions/QuickAssetAction.h"

#include "AssetToolsModule.h"
#include "EditorAssetLibrary.h"
#include "EditorUtilityLibrary.h"
#include "Modules/ModuleManager.h"

void UQuickAssetAction::DuplicateAssets(int32 NumOfDuplicates)
{
	if (NumOfDuplicates <= 0) {
		Print(TEXT("Please enter a valid number"), FColor::Red);
		return;
	}

	
	TArray<FAssetData> SelectedAssetData = UEditorUtilityLibrary::GetSelectedAssetData();
	uint32 Counter = 0;
	for (FAssetData AssetData : SelectedAssetData)
		{
		for (int32 i = 0; i < NumOfDuplicates; ++i)
		{
			const FString SourceAssetPath = AssetData.GetSoftObjectPath().ToString();
			const FString NewDuplicatedAssetName = AssetData.AssetName.ToString() + TEXT("_") + FString::FromInt(i+1);
			const FString NewPathName = FPaths::Combine(AssetData.PackagePath.ToString(), NewDuplicatedAssetName);
			if (UEditorAssetLibrary::DuplicateAsset(SourceAssetPath, NewPathName))
			{
				UEditorAssetLibrary::SaveAsset(NewPathName, false);
				Counter++;
			}
		}
	}
	if (Counter > 0)
	{
		Print(TEXT("Successfully duplicated " + FString::FromInt(Counter) + " files"), FColor::Green);
	}
}
