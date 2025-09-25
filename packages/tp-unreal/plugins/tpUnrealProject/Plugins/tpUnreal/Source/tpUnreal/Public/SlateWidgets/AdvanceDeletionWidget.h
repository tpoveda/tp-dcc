#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
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
	SLATE_END_ARGS()

public:
	void Construct(const FArguments& InArgs);

private:

	TSharedRef<SListView<TSharedPtr<FAssetData>>> ConstructAssetListView();
	void RefreshAssetListView();

	FSlateFontInfo GetEmbossedTextFont() const;

#pragma region RowWidgetForAssetListView
	
	TSharedRef<ITableRow> OnGenerateRowForList(TSharedPtr<FAssetData> AssetData, const TSharedRef<STableViewBase>& OwnerTable);
	TSharedRef<SCheckBox> ConstructCheckBox(const TSharedPtr<FAssetData>& AssetData);
	TSharedRef<STextBlock> ConstructTextForRowWidget(const FString& TextContent, const FSlateFontInfo& FontToUse);
	TSharedRef<SButton> ConstructButtonForRowWidget(const TSharedPtr<FAssetData>& AssetData);
	void OnCheckBoxStateSateChanged(ECheckBoxState NewState, TSharedPtr<FAssetData> AssetData);
	FReply OnDeleteButtonClicked(TSharedPtr<FAssetData> AssetData);

#pragma endregion

#pragma region TabButtons
	
	TSharedRef<SButton> ConstructDeleteAllButton();
	TSharedRef<SButton> ConstructSelectAllButton();
	TSharedRef<SButton> ConstructDeselectAllButton();
	FReply OnDeleteAllButtonClicked();
	FReply OnSelectAllButtonClicked();
	FReply OnDeselectAllButtonClicked();
	TSharedRef<STextBlock> ConstructTextForTabButtons(const FString& TextContent);

#pragma endregion
	
#pragma region Member Variables

	TArray<TSharedPtr<FAssetData>> AssetsData;
	TArray<TSharedPtr<FAssetData>> AssetsDataToDelete;
	TArray<TSharedRef<SCheckBox>> CheckBoxes;
	TSharedPtr<SListView<TSharedPtr<FAssetData>>> ConstructedAssetListView;

#pragma endregion
	
};
