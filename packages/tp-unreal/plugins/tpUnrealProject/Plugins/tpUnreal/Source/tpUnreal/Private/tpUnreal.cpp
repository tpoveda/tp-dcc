// Copyright Epic Games, Inc. All Rights Reserved.

#include "tpUnreal.h"

#include "ContentBrowserModule.h"
#include "DebugHelpers.h"
#include "EditorAssetLibrary.h"
#include "ObjectTools.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"

#define LOCTEXT_NAMESPACE "FtpUnrealModule"

void FtpUnrealModule::StartupModule()
{
	InitContentBrowserExtension();
}

void FtpUnrealModule::ShutdownModule()
{
}

#pragma region ContentBrowserExtension

void FtpUnrealModule::InitContentBrowserExtension()
{
	FContentBrowserModule& ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>(TEXT("ContentBrowser"));
	TArray<FContentBrowserMenuExtender_SelectedPaths>& ContentBrowserMenuExtenders = ContentBrowserModule.GetAllPathViewContextMenuExtenders();
	
	ContentBrowserMenuExtenders.Add(
	FContentBrowserMenuExtender_SelectedPaths::CreateRaw(
		this, &FtpUnrealModule::CustomContentBrowserMenuExtender
		)
	);
}

TSharedRef<FExtender> FtpUnrealModule::CustomContentBrowserMenuExtender(const TArray<FString>& SelectedPaths)
{
	TSharedRef<FExtender> Extender = MakeShareable(new FExtender());
	if (SelectedPaths.Num() > 0)
	{
		Extender->AddMenuExtension(
			FName("Delete"),
			EExtensionHook::After,
			TSharedPtr<FUICommandList>(),
			FMenuExtensionDelegate::CreateRaw(
				this,
				&FtpUnrealModule::AddContentBrowserMenuEntry
			)
		);

		FolderPathsSelected = SelectedPaths;
	}
	return Extender;
}

void FtpUnrealModule::AddContentBrowserMenuEntry(FMenuBuilder& MenuBuilder)
{
	MenuBuilder.AddMenuEntry(
		LOCTEXT("DeleteUnusedAssets", "Delete Unused Assets"),
		LOCTEXT("DeleteUnusedAssetsTooltip", "Safely delete all unused assets under folder"),
		FSlateIcon(),
		FExecuteAction::CreateRaw(
			this, &FtpUnrealModule::OnDeleteUnusedAssetsButtonClicked
		)
	);
}

void FtpUnrealModule::OnDeleteUnusedAssetsButtonClicked()
{
	if (FolderPathsSelected.Num() > 1)
	{
		DebugHelpers::ShowMessageDialog(EAppMsgType::Ok, TEXT("Please select only one folder"));
		return;
	}

	TArray<FString> AssetsPathNames = UEditorAssetLibrary::ListAssets(FolderPathsSelected[0]);
	if (AssetsPathNames.Num() == 0)
	{
		DebugHelpers::ShowMessageDialog(EAppMsgType::Ok, TEXT("No assets found under folder"));
		return;
	}

	if (const EAppReturnType::Type ConfirmResult = DebugHelpers::ShowMessageDialog(EAppMsgType::YesNo, TEXT("Are you sure you want to delete all unused assets under folder?"), false);
		ConfirmResult == EAppReturnType::No) return;

	TArray<FAssetData> UnusedAssetsData;
	for (const FString& AssetPathName : AssetsPathNames)
	{
		if (AssetPathName.Contains(TEXT("Developers")) || AssetPathName.Contains(TEXT("Collections"))) continue;
		if (!UEditorAssetLibrary::DoesAssetExist(AssetPathName)) continue;

		TArray<FString> AssetReferences = UEditorAssetLibrary::FindPackageReferencersForAsset(AssetPathName);
		if (AssetReferences.Num() == 0)
		{
			const FAssetData UnusedAssetData = UEditorAssetLibrary::FindAssetData(AssetPathName);
			UnusedAssetsData.Add(UnusedAssetData);
		}
	}

	if (UnusedAssetsData.Num() > 0)
	{
		ObjectTools::DeleteAssets(UnusedAssetsData);
	}
	else
	{
		DebugHelpers::ShowMessageDialog(EAppMsgType::Ok, TEXT("No unused assets found under folder"));
	}
}

#pragma endregion

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FtpUnrealModule, tpUnreal)