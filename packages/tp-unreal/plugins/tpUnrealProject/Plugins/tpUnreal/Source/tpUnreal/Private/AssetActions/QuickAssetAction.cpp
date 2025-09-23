#include "AssetActions/QuickAssetAction.h"

#include "EditorAssetLibrary.h"
#include "EditorUtilityLibrary.h"

#include "DebugHelpers.h"


void UQuickAssetAction::DuplicateAssets(const int32 NumOfDuplicates)
{
	if (NumOfDuplicates <= 0)
	{
		DebugHelpers::ShowMessageDialog(EAppMsgType::Ok, TEXT("Please enter a valid number"));
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
		DebugHelpers::ShowNotifyInfo(TEXT("Successfully duplicated " + FString::FromInt(Counter) + " assets"));
	}
}

void UQuickAssetAction::AddPrefixes()
{
	TArray<UObject*> SelectedObjects = UEditorUtilityLibrary::GetSelectedAssets();
	uint32 Counter = 0;
	
	for (UObject* SelectedObject : SelectedObjects)
	{
		if (!SelectedObject) continue;

		const FString* PrefixFound = PrefixMap.Find(SelectedObject->GetClass());
		if (!PrefixFound || PrefixFound->IsEmpty())
		{
			DebugHelpers::Print(TEXT("No prefix found for class: ") + SelectedObject->GetClass()->GetName(), FColor::Red);
			continue;
		}

		FString OldName = SelectedObject->GetName();
		if (OldName.StartsWith(*PrefixFound))
		{
			DebugHelpers::Print(TEXT("Object already has prefix: ") + OldName, FColor::Red);
			continue;
		}

		if (SelectedObject->IsA<UMaterialInstanceConstant>())
		{
			OldName.RemoveFromStart(TEXT("M_"));
			OldName.RemoveFromEnd(TEXT("_Inst"));
		}

		const FString NewNameWithPrefix = *PrefixFound + OldName;
		UEditorUtilityLibrary::RenameAsset(SelectedObject, NewNameWithPrefix);
		++Counter;
	}

	if (Counter > 0)
	{
		DebugHelpers::ShowNotifyInfo(TEXT("Successfully renamed " + FString::FromInt(Counter) + " assets"));
	}
}
