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

	TSharedRef<ITableRow> OnGenerateRowForList(TSharedPtr<FAssetData> AssetData, const TSharedRef<STableViewBase>& OwnerTable);
	FSlateFontInfo GetEmbossedTextFont() const;
	TSharedRef<SCheckBox> ConstructCheckBox(const TSharedPtr<FAssetData>& AssetData);
	TSharedRef<SListView<TSharedPtr<FAssetData>>> ConstructAssetListView();
	TSharedRef<STextBlock> ConstructTextForRowWidget(const FString& TextContent, const FSlateFontInfo& FontToUse);
	TSharedRef<SButton> ConstructButtonForRowWidget(const TSharedPtr<FAssetData>& AssetData);
	void OnCheckBoxStateSateChanged(ECheckBoxState NewState, TSharedPtr<FAssetData> AssetData);
	FReply OnDeleteButtonClicked(TSharedPtr<FAssetData> AssetData);
	void RefreshAssetListView();

	TArray<TSharedPtr<FAssetData>> AssetsData;
	TSharedPtr<SListView<TSharedPtr<FAssetData>>> ConstructedAssetListView;
};
