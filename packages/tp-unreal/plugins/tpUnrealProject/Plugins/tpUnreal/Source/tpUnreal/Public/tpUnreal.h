#pragma once

#include "Framework/Docking/TabManager.h"
#include "Modules/ModuleManager.h"
#include "Widgets/Docking/SDockTab.h"

struct FAssetData;
class FMenuBuilder;
class FExtender;

class FtpUnrealModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	/** @brief Deletes a single asset from the asset list.
	 
	 @param AssetDataToDelete The asset data representing the asset to be deleted.
	 @return True if the asset was successfully deleted, otherwise false.
	 */
	bool DeleteSingleAssetForAssetList(const FAssetData& AssetDataToDelete);

	/**
	 * @brief Deletes multiple assets specified in the provided list of asset data.
	 *
	 * @param AssetDataToDelete The list of asset data representing the assets to be deleted.
	 * @return true if one or more assets were successfully deleted, otherwise false.
	 */
	bool DeleteMultipleAssetsForAssetList(const TArray<FAssetData>& AssetDataToDelete);

	/**
	 * @brief Filters the provided list of asset data to identify unused assets and populates the output array with them.
	 *
	 * @param AssetsDataToFilter The array of asset data to be filtered for unused assets.
	 * @param OutUnusedAssetsData The array that will be populated with the unused assets from the input asset data.
	 */
	void ListUnusedAssetsForAssetList(const TArray<TSharedPtr<FAssetData>>& AssetsDataToFilter, TArray<TSharedPtr<FAssetData>>& OutUnusedAssetsData);

	/**
	 * @brief Filters a list of asset data to identify assets with the same name and outputs the filtered assets.
	 *
	 * @param AssetsDataToFilter The array of asset data pointers to be filtered.
	 * @param OutSameNameAssetsData The array where the filtered assets with the same name will be stored.
	 */
	void ListSameNameAssetsForAssetList(const TArray<TSharedPtr<FAssetData>>& AssetsDataToFilter, TArray<TSharedPtr<FAssetData>>& OutSameNameAssetsData);

	void SyncToClickedAssetForAssetList(const FString& AssetPathToSync);
	
private:
	
	/**
	 * @brief Initializes the content browser extension by adding a custom menu extender for selected paths
	 * within the content browser.
	 */
	void InitContentBrowserExtension();

	/**
	 * @brief Extends the Content Browser menu based on the selected paths.
	 *
	 * @param SelectedPaths A list of strings representing the paths selected in the Content Browser.
	 * @return A shared reference to the menu extender that adds custom entries to the Content Browser menu.
	 */
	TSharedRef<FExtender> CustomContentBrowserMenuExtender(const TArray<FString>& SelectedPaths);

	/**
	 * @brief Adds an entry to the Content Browser menu.
	 *
	 * @param MenuBuilder A reference to the menu builder used to construct the Content Browser menu.
	 */
	void AddContentBrowserMenuEntry(FMenuBuilder& MenuBuilder);

	/**
	 * @brief Handles the action triggered by clicking the "Delete Unused Assets" button in the Content Browser menu.
	 *
	 * This method performs the following operations:
	 * - Verifies if exactly one folder is selected. If not, it displays a dialog requesting the user to select only one folder.
	 * - Lists all assets under the selected folder.
	 * - Prompts for confirmation before proceeding with the deletion of unused assets.
	 * - Identifies unused assets by checking asset references and excluding specific folders like "Developers", "Collections",
	 *   "__ExternalActors__", and "__ExternalObjects__".
	 * - Deletes all identified unused assets using ObjectTools after ensuring there are no references.
	 *
	 * If no assets are found or no unused assets exist, respective notification dialogs are displayed to inform the user.
	 */
	void OnDeleteUnusedAssetsButtonClicked();

	/**
	 * @brief Handles the click event for the "Delete Empty Folders" button.
	 *
	 * This method validates and retrieves the folder paths, identifies empty folders,
	 * and optionally deletes them based on user confirmation. It displays appropriate
	 * messages or notifications for the actions performed.
	 *
	 * Key functionality:
	 * - Verifies if folder paths are selected.
	 * - Checks for empty folders, excluding specific directories such as "Developers",
	 *   "Collections", "__ExternalActors__", and "__ExternalObjects__".
	 * - Provides a message dialog to the user indicating the presence of empty folders
	 *   and prompts for confirmation to delete.
	 * - Deletes the empty folders on user consent and shows notifications for the
	 *   number of folders deleted or any failures encountered.
	 */
	void OnDeleteEmptyFoldersButtonClicked();

	/**
	 * @brief Handles the click event for the "Advance Deletion" button within the custom editor tab.
	 */
	void OnAdvanceDeletionButtonClicked();

	/**
	 * @brief Fixes up redirectors within the specified package paths.
	 *
	 * This function identifies and processes redirectors located in the provided
	 * package paths to ensure that asset references are properly fixed.
	 *
	 * @param PackagePaths An array of package paths where redirectors need to be fixed.
	 */
	static void FixUpRedirectors(const TArray<FName>& PackagePaths);

	/**
	 * @brief Extracts and returns the specified capture group from the provided text based on the regex pattern.
	 *
	 * @param Regex A string containing the regular expression used for matching.
	 * @param Text The text in which to search for matches using the regex.
	 * @param CaptureGroup The index of the capture group to retrieve from the match.
	 * @return The string corresponding to the specified capture group if a match is found, otherwise an empty string.
	 */
	static FString MatchAndGetCaptureGroup(const FString& Regex, const FString& Text, int CaptureGroup);

	/**
	 * Extracts and returns the top-level package paths from the provided array of asset data.
	 *
	 * @param Array An array of FAssetData objects containing information about assets.
	 * @return An array of FName objects representing unique top-level package paths.
	 */
	static TArray<FName> GetTopLevelPackagePath(const TArray<FAssetData>& Array);

	/**
	 * @brief Holds the paths of the folders currently selected in the Content Browser.
	 *
	 * These paths are used for operations such as listing assets, deleting unused
	 * assets, or applying fixes to redirectors within the specified paths.
	 */
	TArray<FString> FolderPathsSelected;

	/**
	 * @brief Registers the "Advance Deletion" tab within the Unreal Editor's Tab Manager.
	 * This function binds the spawning behavior of the tab to a custom handler method.
	 */
	void RegisterAdvanceDeletionTab();

	/**
	 * @brief Handles the spawning of the advanced deletion tab within the Unreal Engine editor.
	 *
	 * @param Args The arguments used to configure the advanced deletion tab during spawning.
	 * @return A shared reference to the created advanced deletion tab.
	 */
	TSharedRef<SDockTab> OnSpawnAdvanceDeletionTab(const FSpawnTabArgs& Args);

	/**
	 * @brief Retrieves all asset data objects under the selected folder paths in the Unreal Editor,
	 * excluding specific paths such as "Developers", "Collections", "__ExternalActors__", or "__ExternalObjects__".
	 *
	 * @return An array of shared pointers to FAssetData objects representing the assets found under the selected folder paths.
	 *         If no folder is selected or no assets are found, an empty array is returned.
	 */
	TArray<TSharedPtr<FAssetData>> GetAllAssetsDataUnderSelectedFolder();
};
