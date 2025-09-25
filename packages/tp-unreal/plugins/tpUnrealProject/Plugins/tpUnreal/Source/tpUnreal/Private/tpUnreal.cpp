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
#include "SlateWidgets/AdvanceDeletionWidget.h"

#define LOCTEXT_NAMESPACE "FtpUnrealModule"

void FtpUnrealModule::StartupModule()
{
	InitContentBrowserExtension();
	RegisterAdvanceDeletionTab();
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
		LOCTEXT("DeleteUnusedAssetsTooltip", "Safely delete all unused assets under folder."),
		FSlateIcon(),
		FExecuteAction::CreateRaw(
			this, &FtpUnrealModule::OnDeleteUnusedAssetsButtonClicked
		)
	);

	MenuBuilder.AddMenuEntry(
		LOCTEXT("DeleteEmptyFolder", "Delete Empty Folders"),
		LOCTEXT("DeleteEmptyFoldersTooltip", "Safely delete all empty folders."),
		FSlateIcon(),
		FExecuteAction::CreateRaw(
			this, &FtpUnrealModule::OnDeleteEmptyFoldersButtonClicked
		)
	);

	MenuBuilder.AddMenuEntry(
		LOCTEXT("AdvanceDeletion", "Advance Deletion"),
		LOCTEXT("AdvanceDeletionTooltip", "List assets by specific condition in a tab for deleting."),
		FSlateIcon(),
		FExecuteAction::CreateRaw(
			this, &FtpUnrealModule::OnAdvanceDeletionButtonClicked
		)
	);
}

void FtpUnrealModule::OnDeleteUnusedAssetsButtonClicked()
{
	if (FolderPathsSelected.IsEmpty()) return;
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

void FtpUnrealModule::OnDeleteEmptyFoldersButtonClicked()
{
	if (FolderPathsSelected.IsEmpty()) return;
	
	TArray<FString> FolderPaths = UEditorAssetLibrary::ListAssets(FolderPathsSelected[0], true, true);

	FixUpRedirectors(TArray<FName>({"/Game"}));
	
	int32 Counter = 0;
	FString EmptyFolderPathsNames;
	TArray<FString> EmptyFolderPaths;
	for (const FString& FolderPath : FolderPaths)
	{
		if (FolderPath.Contains(TEXT("Developers")) ||
		FolderPath.Contains(TEXT("Collections")) ||
		FolderPath.Contains(TEXT("__ExternalActors__")) ||
		FolderPath.Contains(TEXT("__ExternalObjects__")))
			continue;

		FString Path = FolderPath;
		Path.RemoveAt(Path.Len()-1);
		if (!UEditorAssetLibrary::DoesDirectoryExist(Path)) continue;
		if (UEditorAssetLibrary::DoesDirectoryHaveAssets(Path)) continue;

		EmptyFolderPathsNames.Append(Path);
		EmptyFolderPathsNames.Append(TEXT("\n"));
		EmptyFolderPaths.Add(Path);
	}

	if (EmptyFolderPaths.IsEmpty())
	{
		DebugHelpers::ShowMessageDialog(EAppMsgType::Ok, TEXT("No empty folders found"), false);
		return;
	}

	if (DebugHelpers::ShowMessageDialog(
		EAppMsgType::OkCancel,
		TEXT("Empty folders found in:\n") + EmptyFolderPathsNames + TEXT("\nWould you like to delete all?"),
		false) != EAppReturnType::Ok)
		return;

	for (const FString& EmptyFolderPath : EmptyFolderPaths)
	{
		if (UEditorAssetLibrary::DeleteDirectory(EmptyFolderPath))
		{
			++Counter;
		}
		else
		{
			DebugHelpers::Print(TEXT("Failed to delete folder: ") + EmptyFolderPath, FColor::Red);
		}
	}

	if (Counter > 0)
	{
		DebugHelpers::ShowNotifyInfo(TEXT("Successfully deleted " + FString::FromInt(Counter) + " folders"));
	}
}

void FtpUnrealModule::OnAdvanceDeletionButtonClicked()
{
	FGlobalTabmanager::Get()->TryInvokeTab(FName("AdvanceDeletion"));
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

FString FtpUnrealModule::MatchAndGetCaptureGroup(const FString& Regex, const FString& Text, const int CaptureGroup)
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

#pragma region CustomEditorTab

void FtpUnrealModule::RegisterAdvanceDeletionTab()
{
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(
		"AdvanceDeletion",
		FOnSpawnTab::CreateRaw(
			this,
			&FtpUnrealModule::OnSpawnAdvanceDeletionTab
		)
	).SetDisplayName(LOCTEXT("AdvanceDeletionTabName", "Advance Deletion"));
}

TSharedRef<SDockTab> FtpUnrealModule::OnSpawnAdvanceDeletionTab(const FSpawnTabArgs& Args)
{
	return SNew(SDockTab).TabRole(ETabRole::NomadTab)
	[
		SNew(SAdvanceDeletionTab)
		.AssetsData(GetAllAssetsDataUnderSelectedFolder())
	];
}

TArray<TSharedPtr<FAssetData>> FtpUnrealModule::GetAllAssetsDataUnderSelectedFolder()
{
	TArray<TSharedPtr<FAssetData>> AvailableAssetsData;
	if (FolderPathsSelected.IsEmpty()) return AvailableAssetsData;
	
	TArray<FString> AssetsPathNames = UEditorAssetLibrary::ListAssets(FolderPathsSelected[0]);
	for (const FString& AssetPathName : AssetsPathNames)
	{
		if (AssetPathName.Contains(TEXT("Developers")) ||
			AssetPathName.Contains(TEXT("Collections")) ||
			AssetPathName.Contains(TEXT("__ExternalActors__")) ||
			AssetPathName.Contains(TEXT("__ExternalObjects__")))
			continue;
		if (!UEditorAssetLibrary::DoesAssetExist(AssetPathName)) continue;

		const FAssetData AssetData = UEditorAssetLibrary::FindAssetData(AssetPathName);
		AvailableAssetsData.Add(MakeShared<FAssetData>(AssetData));
	}

	return AvailableAssetsData;
}

#pragma endregion

#pragma region ProcessDataForAdvanceDeletion

bool FtpUnrealModule::DeleteSingleAssetForAssetList(const FAssetData& AssetDataToDelete)
{
	if (ObjectTools::DeleteAssets({AssetDataToDelete}) > 0) return true;
	return false;
}

#pragma endregion

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FtpUnrealModule, tpUnreal)