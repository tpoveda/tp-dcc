// Copyright Epic Games, Inc. All Rights Reserved.

#include "tpUnreal.h"

#include "AssetToolsModule.h"
#include "AssetViewUtils.h"
#include "ContentBrowserModule.h"
#include "DebugHelpers.h"
#include "EditorAssetLibrary.h"
#include "ObjectTools.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Internationalization/Regex.h"

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

	if (const EAppReturnType::Type ConfirmResult = DebugHelpers::ShowMessageDialog(
		EAppMsgType::YesNo,
		TEXT("Are you sure you want to delete all unused assets under folder?"),
		false);
		ConfirmResult == EAppReturnType::No) return;
	
	TArray<FAssetData> UnusedAssetsData;
	for (const FString& AssetPathName : AssetsPathNames)
	{
		if (AssetPathName.Contains(TEXT("Developers")) ||
			AssetPathName.Contains(TEXT("Collections")) ||
			AssetPathName.Contains(TEXT("__ExternalActors__")) ||
			AssetPathName.Contains(TEXT("__ExternalObjects__"))) continue;
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
		FixUpRedirectors(GetTopLevelPackagePath(UnusedAssetsData));
		ObjectTools::DeleteAssets(UnusedAssetsData);
	}
	else
	{
		DebugHelpers::ShowMessageDialog(EAppMsgType::Ok, TEXT("No unused assets found under folder"));
	}
}

void FtpUnrealModule::FixUpRedirectors(const TArray<FName>& PackagePaths)
{
	TArray<UObjectRedirector*> RedirectorsToFixArray;
	const IAssetRegistry& AssetRegistry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();

	// Form a filter from the paths.
	FARFilter Filter;
	Filter.bRecursiveClasses = true;
	Filter.PackagePaths.Append(PackagePaths);
	Filter.ClassPaths.Add(UObjectRedirector::StaticClass()->GetClassPathName());

	// Query for a list of assets in the selected paths.
	TArray<FAssetData> AssetList;
	AssetRegistry.GetAssets(Filter, AssetList);
	if (AssetList.Num() == 0) return;
	TArray<FString> ObjectPaths;
	for (const FAssetData& Asset : AssetList)
	{			
		ObjectPaths.Add(Asset.GetObjectPathString());	
	}

	AssetViewUtils::FLoadAssetsSettings Settings;
	Settings.bFollowRedirectors = false;
	Settings.bAllowCancel = true;
	TArray<UObject*> Objects;
	if (AssetViewUtils::ELoadAssetsResult Result = AssetViewUtils::LoadAssetsIfNeeded(ObjectPaths,Objects,Settings); Result != AssetViewUtils::ELoadAssetsResult::Cancelled)
	{
		// Transform Objects array to ObjectRedirectors array
		TArray<UObjectRedirector*> Redirectors;
		for (UObject* Object : Objects)
		{
			Redirectors.Add(CastChecked<UObjectRedirector>(Object));
		}
	
		// Load the asset tools module
		FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
		AssetToolsModule.Get().FixupReferencers(Redirectors);
	}
}

FString FtpUnrealModule::MatchAndGetCaptureGroup(const FString& Regex, const FString& Text, int CaptureGroup)
{
	const FRegexPattern Pattern(Regex);
	FRegexMatcher Matcher(Pattern, Text);
	if (Matcher.FindNext())
	{
		return Matcher.GetCaptureGroup(CaptureGroup);
	}
	return "";
}

TArray<FName> FtpUnrealModule::GetTopLevelPackagePath(const TArray<FAssetData>& Array)
{
	TMap<FName, int32> TopLevelPackagePath;
	for (const auto& AssetData : Array)
	{
		FString AssetPath = AssetData.GetSoftObjectPath().ToString();
		FString TopLevelPath = MatchAndGetCaptureGroup(TEXT("^(/[^/]*)"), AssetPath, 1);
		TopLevelPackagePath.FindOrAdd(*TopLevelPath);
	} 
 
	TArray<FName> Result;
	TopLevelPackagePath.GetKeys(Result);
	
	return Result;
}

#pragma endregion

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FtpUnrealModule, tpUnreal)