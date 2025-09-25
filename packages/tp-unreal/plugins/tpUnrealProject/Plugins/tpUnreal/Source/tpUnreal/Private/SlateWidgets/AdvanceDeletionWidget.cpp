#include "SlateWidgets/AdvanceDeletionWidget.h"

#include "tpUnreal.h"
#include "DebugHelpers.h"
#include "AssetRegistry/AssetData.h"
#include "Components/VerticalBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Views/SListView.h"

void SAdvanceDeletionTab::Construct(const FArguments& InArgs)
{
	bCanSupportFocus = true;

	AssetsData = InArgs._AssetsData;
	FSlateFontInfo TitleTextFont = GetEmbossedTextFont();
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
		.VAlign(VAlign_Fill)	// Needed to ensure scrollbox works as expected.
		[
			SNew(SScrollBox)
			+ SScrollBox::Slot()
			[
				ConstructAssetListView()
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
	if (!AssetData.IsValid()) return SNew(STableRow<TSharedPtr<FAssetData>>, OwnerTable);

	const FString DisplayAssetClassName = AssetData->AssetClassPath.GetAssetName().ToString();
	const FString DisplayAssetName = AssetData->AssetName.ToString();

	FSlateFontInfo AssetClassNameFont = GetEmbossedTextFont();
	AssetClassNameFont.Size = 10.0f;
	FSlateFontInfo AssetNameFont = GetEmbossedTextFont();
	AssetNameFont.Size = 11.5f;
	
	TSharedRef<STableRow<TSharedPtr<FAssetData>>> ListViewRowWidget =
	SNew(STableRow<TSharedPtr<FAssetData>>, OwnerTable)
		.Padding(FMargin(2.5f))
	[
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.HAlign(HAlign_Left)
		.VAlign(VAlign_Center)
		.FillWidth(0.05f)
		[
			ConstructCheckBox(AssetData)
		]
		+ SHorizontalBox::Slot()
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Fill)
		.FillWidth(0.6f)
		[
			ConstructTextForRowWidget(DisplayAssetClassName, AssetClassNameFont)
		]
		+ SHorizontalBox::Slot()
		.HAlign(HAlign_Left)
		.VAlign(VAlign_Fill)
		[
			ConstructTextForRowWidget(DisplayAssetName, AssetNameFont)
		]
		+ SHorizontalBox::Slot()
		.HAlign(HAlign_Right)
		.VAlign(VAlign_Fill)
		[
			ConstructButtonForRowWidget(AssetData)
		]
	];

	return ListViewRowWidget;
}

TSharedRef<SCheckBox> SAdvanceDeletionTab::ConstructCheckBox(const TSharedPtr<FAssetData>& AssetData)
{
	TSharedRef<SCheckBox> ConstructedCheckBox = SNew(SCheckBox)
		.Type(ESlateCheckBoxType::CheckBox)
		.OnCheckStateChanged(this, &SAdvanceDeletionTab::OnCheckBoxStateSateChanged, AssetData)
		.Visibility(EVisibility::Visible);

	return ConstructedCheckBox;
}

TSharedRef<SListView<TSharedPtr<FAssetData>>> SAdvanceDeletionTab::ConstructAssetListView()
{
	ConstructedAssetListView = SNew(SListView<TSharedPtr<FAssetData>>)
	.ListItemsSource(&AssetsData)
	.OnGenerateRow(this, &SAdvanceDeletionTab::OnGenerateRowForList);

	return ConstructedAssetListView.ToSharedRef();
}

TSharedRef<STextBlock> SAdvanceDeletionTab::ConstructTextForRowWidget(const FString& TextContent,
                                                                      const FSlateFontInfo& FontToUse)
{
	TSharedRef<STextBlock> ConstructedTextBlock = SNew(STextBlock)
	.Text(FText::FromString(TextContent))
	.Font(FontToUse)
	.ColorAndOpacity(FColor::White);

	return ConstructedTextBlock;
}

TSharedRef<SButton> SAdvanceDeletionTab::ConstructButtonForRowWidget(const TSharedPtr<FAssetData>& AssetData)
{
	TSharedRef<SButton> ConstructedButton = SNew(SButton)
	.Text(FText::FromString("Delete"))
	.OnClicked(this, &SAdvanceDeletionTab::OnDeleteButtonClicked, AssetData);

	return ConstructedButton;
}

FSlateFontInfo SAdvanceDeletionTab::GetEmbossedTextFont() const
{
	return FCoreStyle::Get().GetFontStyle(FName("EmbossedText"));
}

void SAdvanceDeletionTab::OnCheckBoxStateSateChanged(ECheckBoxState NewState, TSharedPtr<FAssetData> AssetData)
{
	switch (NewState)
	{
	case ECheckBoxState::Unchecked:
		DebugHelpers::Print(FString::Printf(TEXT("Asset %s has been unchecked"), *AssetData->AssetName.ToString()), FColor::Red);
		break;
	case ECheckBoxState::Checked:
		DebugHelpers::Print(FString::Printf(TEXT("Asset %s has been checked"), *AssetData->AssetName.ToString()), FColor::Green);
		break;
	case ECheckBoxState::Undetermined:
		break;
	default:
		break;
	}
}

FReply SAdvanceDeletionTab::OnDeleteButtonClicked(TSharedPtr<FAssetData> AssetData)
{
	FtpUnrealModule& tpUnrealModule = FModuleManager::LoadModuleChecked<FtpUnrealModule>(TEXT("tpUnreal"));

	if (tpUnrealModule.DeleteSingleAssetForAssetList(*AssetData.Get()))
	{
		if (AssetsData.Contains(AssetData))
		{
			AssetsData.Remove(AssetData);
		}
		RefreshAssetListView();
	}
	
	return FReply::Handled();
}

void SAdvanceDeletionTab::RefreshAssetListView()
{
	if (!ConstructedAssetListView.IsValid()) return;

	ConstructedAssetListView->RebuildList();
		
}
