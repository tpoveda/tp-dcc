#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Views/SListView.h"


class STextBlock;
class SCheckBox;
class SButton;
class STableViewBase;
class ITableRow;

class SAdvanceDeletionTab : public SCompoundWidget
{
	SLATE_BEGIN_ARGS(SAdvanceDeletionTab) {}
		SLATE_ARGUMENT(TArray<TSharedPtr<FAssetData>>, AssetsData)
		SLATE_ARGUMENT(FString, CurrentSelectedFolder);
	SLATE_END_ARGS()

public:
	void Construct(const FArguments& InArgs);

private:

	TSharedRef<SListView<TSharedPtr<FAssetData>>> ConstructAssetListView();
	void RefreshAssetListView();

	FSlateFontInfo GetEmbossedTextFont() const;
	
	TSharedRef<SComboBox<TSharedPtr<FString>>> ConstructComboBox();
	TSharedRef<STextBlock> ConstructHelpTextForComboBox(const FString& TextContent, ETextJustify::Type TextJustify);
	TArray<TSharedPtr<FString>> ComboBoxSourceItems;
	TSharedRef<SWidget> OnGenerateComboBoxContent(TSharedPtr<FString> SourceItem);
	void OnComboBoxSelectionChanged(TSharedPtr<FString> SelectedOption, ESelectInfo::Type SelectInfo);
	TSharedPtr<STextBlock> ComboBoxContentContainer;
	
	TSharedRef<ITableRow> OnGenerateRowForList(TSharedPtr<FAssetData> AssetData, const TSharedRef<STableViewBase>& OwnerTable);
	void OnRowWidgetMouseButtonClicked(TSharedPtr<FAssetData> AssetData);
	TSharedRef<SCheckBox> ConstructCheckBox(const TSharedPtr<FAssetData>& AssetData);
	TSharedRef<STextBlock> ConstructTextForRowWidget(const FString& TextContent, const FSlateFontInfo& FontToUse);
	TSharedRef<SButton> ConstructButtonForRowWidget(const TSharedPtr<FAssetData>& AssetData);
	void OnCheckBoxStateSateChanged(ECheckBoxState NewState, TSharedPtr<FAssetData> AssetData);
	FReply OnDeleteButtonClicked(TSharedPtr<FAssetData> AssetData);
	
	TSharedRef<SButton> ConstructDeleteAllButton();
	TSharedRef<SButton> ConstructSelectAllButton();
	TSharedRef<SButton> ConstructDeselectAllButton();
	FReply OnDeleteAllButtonClicked();
	FReply OnSelectAllButtonClicked();
	FReply OnDeselectAllButtonClicked();
	TSharedRef<STextBlock> ConstructTextForTabButtons(const FString& TextContent);
	
	TArray<TSharedPtr<FAssetData>> AssetsData;
	TArray<TSharedPtr<FAssetData>> DisplayedAssetsData;
	TArray<TSharedPtr<FAssetData>> AssetsDataToDelete;
	TArray<TSharedRef<SCheckBox>> CheckBoxes;
	TSharedPtr<SListView<TSharedPtr<FAssetData>>> ConstructedAssetListView;
	
};
