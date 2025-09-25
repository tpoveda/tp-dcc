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

private:

#pragma region ContentBrowserExtension

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
	
#pragma endregion

#pragma region CustomEditorTab

	void RegisterAdvanceDeletionTab();
	TSharedRef<SDockTab> OnSpawnAdvanceDeletionTab(const FSpawnTabArgs& Args);
	TArray<TSharedPtr<FAssetData>> GetAllAssetsDataUnderSelectedFolder();
	
#pragma endregion
	
public:
	
#pragma region ProcessDataForAdvanceDeletion

	bool DeleteSingleAssetForAssetList(const FAssetData& AssetDataToDelete);
	
#pragma endregion

};
