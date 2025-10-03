#include "SlateWidgets/AdvanceDeletionWidget.h"

#include "tpUnreal.h"
#include "DebugHelpers.h"
#include "AssetRegistry/AssetData.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Views/SListView.h"

#define ListAll TEXT("List All Available Assets")
#define ListUnused TEXT("List Unused Assets")
#define ListSameName TEXT("List Assets With Same Name")

void SAdvanceDeletionTab::Construct(const FArguments& InArgs)
{
	bCanSupportFocus = true;

	AssetsData = InArgs._AssetsData;
	DisplayedAssetsData = AssetsData; 
	
	CheckBoxes.Empty();
	AssetsDataToDelete.Empty();
    ComboBoxSourceItems.Empty();
    
	ComboBoxSourceItems.Add(MakeShared<FString>(ListAll));
	ComboBoxSourceItems.Add(MakeShared<FString>(ListUnused));
	ComboBoxSourceItems.Add(MakeShared<FString>(ListSameName));
	
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
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				ConstructComboBox()
			]
			+ SHorizontalBox::Slot()
			.FillWidth(0.6f)
			[
				ConstructHelpTextForComboBox(TEXT("Specify the listing condition in the drop down. Left mouse click to go to where asset is located"), ETextJustify::Center)
			]
			+ SHorizontalBox::Slot()
			.FillWidth(0.1f)
			[
				ConstructHelpTextForComboBox(TEXT("Current Folder:\n") + InArgs._CurrentSelectedFolder, ETextJustify::Right)
			]
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
			+ SHorizontalBox::Slot()
			.FillWidth(10.0f)
			.Padding(5.0f)
			[
				ConstructDeleteAllButton()
			]
			+ SHorizontalBox::Slot()
			.FillWidth(10.0f)
			.Padding(5.0f)
			[
				ConstructSelectAllButton()
			]
			+ SHorizontalBox::Slot()
			.FillWidth(10.0f)
			.Padding(5.0f)
			[
				ConstructDeselectAllButton()
			]
		]
	];
}

TSharedRef<SListView<TSharedPtr<FAssetData>>> SAdvanceDeletionTab::ConstructAssetListView()
{
	ConstructedAssetListView = SNew(SListView<TSharedPtr<FAssetData>>)
	.ListItemsSource(&DisplayedAssetsData)
	.OnGenerateRow(this, &SAdvanceDeletionTab::OnGenerateRowForList)
	.OnMouseButtonClick(this, &SAdvanceDeletionTab::OnRowWidgetMouseButtonClicked);

	return ConstructedAssetListView.ToSharedRef();
}

void SAdvanceDeletionTab::RefreshAssetListView()
{
	CheckBoxes.Empty();
	AssetsDataToDelete.Empty();

	if (!ConstructedAssetListView.IsValid()) return;
	ConstructedAssetListView->RebuildList();
		
}

FSlateFontInfo SAdvanceDeletionTab::GetEmbossedTextFont() const
{
	return FCoreStyle::Get().GetFontStyle(FName("EmbossedText"));
}

TSharedRef<SComboBox<TSharedPtr<FString>>> SAdvanceDeletionTab::ConstructComboBox()
{
	TSharedRef<SComboBox<TSharedPtr<FString>>> ConstructedComboBox = SNew(SComboBox<TSharedPtr<FString>>)
		.OptionsSource(&ComboBoxSourceItems)
		.OnGenerateWidget(this, &SAdvanceDeletionTab::OnGenerateComboBoxContent)
		.OnSelectionChanged(this, &SAdvanceDeletionTab::OnComboBoxSelectionChanged)
		[
			SAssignNew(ComboBoxContentContainer, STextBlock)
			.Text(FText::FromString(ListAll))
		];		

	return ConstructedComboBox;
}

TSharedRef<STextBlock> SAdvanceDeletionTab::ConstructHelpTextForComboBox(const FString& TextContent,
	ETextJustify::Type TextJustify)
{
	TSharedRef<STextBlock> ConstructedHelpText = SNew(STextBlock)
		.Text(FText::FromString(TextContent))
		.Justification(TextJustify)
		.AutoWrapText(true);

	return ConstructedHelpText;
}

TSharedRef<SWidget> SAdvanceDeletionTab::OnGenerateComboBoxContent(TSharedPtr<FString> SourceItem)
{
	TSharedRef<STextBlock> ConstructedComboText = SNew(STextBlock)
		.Text(FText::FromString(*SourceItem.Get()));

	return ConstructedComboText;
}

void SAdvanceDeletionTab::OnComboBoxSelectionChanged(TSharedPtr<FString> SelectedOption, ESelectInfo::Type SelectInfo)
{
	DebugHelpers::Print(*SelectedOption.Get(), FColor::Cyan);

	ComboBoxContentContainer->SetText(FText::FromString(*SelectedOption.Get()));

	FtpUnrealModule& tpUnrealModule = FModuleManager::LoadModuleChecked<FtpUnrealModule>(TEXT("tpUnreal"));
	if (*SelectedOption.Get() == ListAll)
	{
		DisplayedAssetsData = AssetsData;
		RefreshAssetListView();
	}
	else if (*SelectedOption.Get() == ListUnused)
	{
		tpUnrealModule.ListUnusedAssetsForAssetList(AssetsData, DisplayedAssetsData);
		RefreshAssetListView();
	}
	else if (*SelectedOption.Get() == ListSameName)
	{
		tpUnrealModule.ListSameNameAssetsForAssetList(AssetsData, DisplayedAssetsData);
		RefreshAssetListView();
	}
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

void SAdvanceDeletionTab::OnRowWidgetMouseButtonClicked(TSharedPtr<FAssetData> AssetData)
{
	FtpUnrealModule& tpUnrealModule = FModuleManager::LoadModuleChecked<FtpUnrealModule>(TEXT("tpUnreal"));
	tpUnrealModule.SyncToClickedAssetForAssetList(AssetData->GetObjectPathString());
}

TSharedRef<SCheckBox> SAdvanceDeletionTab::ConstructCheckBox(const TSharedPtr<FAssetData>& AssetData)
{
	TSharedRef<SCheckBox> ConstructedCheckBox = SNew(SCheckBox)
		.Type(ESlateCheckBoxType::CheckBox)
		.OnCheckStateChanged(this, &SAdvanceDeletionTab::OnCheckBoxStateSateChanged, AssetData)
		.Visibility(EVisibility::Visible);

	CheckBoxes.Add(ConstructedCheckBox);
	
	return ConstructedCheckBox;
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

void SAdvanceDeletionTab::OnCheckBoxStateSateChanged(ECheckBoxState NewState, TSharedPtr<FAssetData> AssetData)
{
	switch (NewState)
	{
	case ECheckBoxState::Unchecked:
		if (AssetsDataToDelete.Contains(AssetData))
		{
			AssetsDataToDelete.Remove(AssetData);
		}
		break;
	case ECheckBoxState::Checked:
		AssetsDataToDelete.AddUnique(AssetData);
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

		if (DisplayedAssetsData.Contains(AssetData))
		{
			DisplayedAssetsData.Remove(AssetData);
		}
		
		RefreshAssetListView();
	}
	
	return FReply::Handled();
}


TSharedRef<SButton> SAdvanceDeletionTab::ConstructDeleteAllButton()
{
	TSharedRef<SButton> DeleteAllButton = SNew(SButton)
		.ContentPadding(FMargin(5.0f))
		.OnClicked(this, &SAdvanceDeletionTab::OnDeleteAllButtonClicked);
	DeleteAllButton->SetContent(ConstructTextForTabButtons(TEXT("Delete Selected")));

	return DeleteAllButton;
}

TSharedRef<SButton> SAdvanceDeletionTab::ConstructSelectAllButton()
{
	TSharedRef<SButton> SelectAllButton = SNew(SButton)
		.ContentPadding(FMargin(5.0f))
		.OnClicked(this, &SAdvanceDeletionTab::OnSelectAllButtonClicked);
	SelectAllButton->SetContent(ConstructTextForTabButtons(TEXT("Select All")));

	return SelectAllButton;
}

TSharedRef<SButton> SAdvanceDeletionTab::ConstructDeselectAllButton()
{
	TSharedRef<SButton> DeselectAllButton = SNew(SButton)
		.ContentPadding(FMargin(5.0f))
		.OnClicked(this, &SAdvanceDeletionTab::OnDeselectAllButtonClicked);
	DeselectAllButton->SetContent(ConstructTextForTabButtons(TEXT("Deselect All")));

	return DeselectAllButton;
}

FReply SAdvanceDeletionTab::OnDeleteAllButtonClicked()
{
	if (AssetsDataToDelete.IsEmpty())
	{
		DebugHelpers::ShowMessageDialog(EAppMsgType::Ok, TEXT("No assets selected"));
		return FReply::Handled();
	}

	TArray<FAssetData> AssetsToDelete;
	for (const TSharedPtr<FAssetData>& AssetData : AssetsDataToDelete)
	{
		AssetsToDelete.AddUnique(*AssetData.Get());
	}

	FtpUnrealModule& tpUnrealModule = FModuleManager::LoadModuleChecked<FtpUnrealModule>(TEXT("tpUnreal"));
	const bool bAssetsDeleted = tpUnrealModule.DeleteMultipleAssetsForAssetList(AssetsToDelete);
	if (bAssetsDeleted)
	{
		for (const TSharedPtr<FAssetData>& DeletedData : AssetsDataToDelete)
		{
			if (AssetsData.Contains(DeletedData))
			{
				AssetsData.Remove(DeletedData);
			}

			if (DisplayedAssetsData.Contains(DeletedData))
			{
				DisplayedAssetsData.Remove(DeletedData);
			}
		}
		
		RefreshAssetListView();
	}
	
	return FReply::Handled();
}

FReply SAdvanceDeletionTab::OnSelectAllButtonClicked()
{
	if (CheckBoxes.IsEmpty()) return FReply::Handled();
	
	for (const TSharedRef<SCheckBox>& CheckBox : CheckBoxes)
	{
		CheckBox->SetIsChecked(ECheckBoxState::Checked);
	}
	
	return FReply::Handled();
}

FReply SAdvanceDeletionTab::OnDeselectAllButtonClicked()
{
	if (CheckBoxes.IsEmpty()) return FReply::Handled();
	
	for (const TSharedRef<SCheckBox>& CheckBox : CheckBoxes)
	{
		CheckBox->SetIsChecked(ECheckBoxState::Unchecked);
	}
	
	return FReply::Handled();
}

TSharedRef<STextBlock> SAdvanceDeletionTab::ConstructTextForTabButtons(const FString& TextContent)
{
	FSlateFontInfo ButtonTextFont = GetEmbossedTextFont();
	ButtonTextFont.Size = 15.0f;
	
	TSharedRef<STextBlock> ConstructedTextBlock = SNew(STextBlock)
		.Text(FText::FromString(TextContent))
		.Font(ButtonTextFont)
		.Justification(ETextJustify::Center);

	return ConstructedTextBlock;
}