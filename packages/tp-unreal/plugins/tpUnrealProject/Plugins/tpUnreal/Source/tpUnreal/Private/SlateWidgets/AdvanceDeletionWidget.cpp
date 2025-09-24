#include "SlateWidgets/AdvanceDeletionWidget.h"

#include "AssetRegistry/AssetData.h"
#include "Components/VerticalBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Views/SListView.h"

void SAdvanceDeletionTab::Construct(const FArguments& InArgs)
{
	bCanSupportFocus = true;

	AssetsData = InArgs._AssetsData;
	FSlateFontInfo TitleTextFont = FCoreStyle::Get().GetFontStyle(FName("EmbossedText"));
	TitleTextFont.Size = 30.0f;
	
	ChildSlot
	[
		SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(STextBlock)
			.Text(FText::FromString("Advance Deletion"))
			.Font(TitleTextFont)
			.Justification(ETextJustify::Center)
			.ColorAndOpacity(FColor::White)
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SHorizontalBox)
		]
		+ SVerticalBox::Slot()
		.VAlign(VAlign_Fill)
		[
			SNew(SScrollBox)
			+ SScrollBox::Slot()
			[
				SNew(SListView<TSharedPtr<FAssetData>>)
				.ListItemsSource(&AssetsData)
				.OnGenerateRow(this, &SAdvanceDeletionTab::OnGenerateRowForList)
			]
		]
		+ SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SHorizontalBox)
		]
	];
}

TSharedRef<ITableRow> SAdvanceDeletionTab::OnGenerateRowForList(TSharedPtr<FAssetData> AssetData,
	const TSharedRef<STableViewBase>& OwnerTable)
{
	const FString DisplayAssetName = AssetData->AssetName.ToString();
	TSharedRef<STableRow<TSharedPtr<FAssetData>>> ListViewRowWidget =
	SNew(STableRow<TSharedPtr<FAssetData>>, OwnerTable)
	[
		SNew(STextBlock)
		.Text(FText::FromString(DisplayAssetName))
	];

	return ListViewRowWidget;
}
