#include "StpLevelSelectorWidget.h"

#include "TPLevelSelectorSettings.h"
#include "AssetRegistry/AssetData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Components/HorizontalBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

FLevelSelectorItem::FLevelSelectorItem(const FAssetData& InAssetData)
	: AssetData(InAssetData)
{
	DisplayName = AssetData.AssetName.ToString();
	PackagePath = AssetData.GetSoftObjectPath().GetLongPackageName();
	SoftPath = AssetData.GetSoftObjectPath();
}

void StpLevelSelectorWidget::Construct(const FArguments& InArgs)
{
	DefaultLevelIcon = FAppStyle::GetBrush("LevelEditor.Tabs.Levels");
	RefreshIconBrush = FAppStyle::GetBrush("Icons.Refresh");

	PopulateLevels();
	
	ChildSlot
	[
		SNew(SBox)
		.Padding(FMargin(12.0f, 2.0f))
		.HeightOverride(32)
		.MinDesiredWidth(320)
		.MaxDesiredWidth(480)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			.Padding(0, 0, 8, 0)
			[
				SNew(STextBlock)
				.Text(FText::FromString("Level:"))
			]
			+ SHorizontalBox::Slot()
			.FillWidth(1.0f)
			.VAlign(VAlign_Center)
			[
				SAssignNew(LevelComboBox, SComboBox<TSharedPtr<FLevelSelectorItem>>)
				.OptionsSource(&AvailableLevels)
				.OnGenerateWidget(this, &StpLevelSelectorWidget::OnGenerateWidgetForComboBox)
				.MaxListHeight(480.0f)
				[
					SAssignNew(ComboBoxContentContainer, SBox)
					.VAlign(VAlign_Center)
					[
						SNew(STextBlock)
						.Text(FText::FromString(TEXT("Select a Level...")))
					]
				]
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			.Padding(FMargin(4, 0, 0, 0))
			[
				SNew(SBox)
				.WidthOverride(28)
				.HeightOverride(28)
				[
					SNew(SOverlay)
					+ SOverlay::Slot()
					.HAlign(HAlign_Fill)
					.VAlign(VAlign_Fill)
					[
						SNew(SButton)
						.ContentPadding(0)
						[
							SNew(STextBlock)
							.Text(FText::FromString("Refresh"))
						]
					]
					+ SOverlay::Slot()
					.HAlign(HAlign_Center)
					.VAlign(VAlign_Center)
					.Padding(4.0f)
					[
						SNew(SImage)
						.DesiredSizeOverride(FVector2D(20, 20))
						.Visibility(EVisibility::HitTestInvisible)
					]
				]
			]
		]
	];
}

void StpLevelSelectorWidget::PopulateLevels()
{
	AllLevels.Empty();

	const FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
	TArray<FAssetData> AssetData;
	AssetRegistryModule.Get().GetAssetsByClass(UWorld::StaticClass()->GetClassPathName(), AssetData);

	const UTpLevelSelectorSettings* Settings = GetDefault<UTpLevelSelectorSettings>();
	if (!Settings) return;

	for (const FSoftObjectPath& FavoritePath : Settings->FavoriteLevels)
	{
		if (!FavoritePath.IsValid()) continue;
		if (const FAssetData FavoriteAsset = AssetRegistryModule.Get().GetAssetByObjectPath(FavoritePath); FavoriteAsset.IsValid())
		{
			AllLevels.Add(FLevelSelectorItem::Create(FavoriteAsset));
		}
	}

	TMap<FName, TSharedRef<FLevelSelectorItem>> LevelsByPkg;
	for (const TSharedPtr<FLevelSelectorItem>& Existing : AllLevels)
	{
		LevelsByPkg.Add(FName(*Existing->PackagePath), Existing.ToSharedRef());
	}
	
	for (const FAssetData& Asset : AssetData)
	{
		const FName PkgName = Asset.PackageName;
		if (!PkgName.ToString().StartsWith(TEXT("/Game/"))) continue;
		LevelsByPkg.FindOrAdd(PkgName, FLevelSelectorItem::Create(Asset));
	}

	AllLevels.Reset(LevelsByPkg.Num());
	for (TPair<FName, TSharedRef<FLevelSelectorItem>>& KeyValue : LevelsByPkg)
	{
		AllLevels.Add(KeyValue.Value);
	}

	SortLevels();

	ApplyFilters();
}

void StpLevelSelectorWidget::SortLevels()
{
	const UTpLevelSelectorSettings* Settings = GetDefault<UTpLevelSelectorSettings>();
	if (!Settings)
	{
		Algo::StableSort(AllLevels, [](
			const TSharedPtr<FLevelSelectorItem>& A,
			const TSharedPtr<FLevelSelectorItem>& B)
		{
			const FName AName = A->AssetData.PackageName;
			const FName BName = B->AssetData.PackageName;
			if (AName != BName) return AName.LexicalLess(BName);
			return A->AssetData.AssetName.LexicalLess(B->AssetData.AssetName);
		});
		return;
	}

	// Build a set of favorite package once.
	TSet<FName> FavoritePackages;
	FavoritePackages.Reserve(Settings->FavoriteLevels.Num());
	for (const FSoftObjectPath& P : Settings->FavoriteLevels)
	{
		FavoritePackages.Add(P.GetLongPackageFName());
	}

	Algo::StableSort(AllLevels, [&FavoritePackages](
		const TSharedPtr<FLevelSelectorItem>& A,
		const TSharedPtr<FLevelSelectorItem>& B)
	{
		// 1) Sort by Favorites.
		const bool AIsFav = FavoritePackages.Contains(A->AssetData.PackageName);
		const bool BIsFav = FavoritePackages.Contains(B->AssetData.PackageName);
		if (AIsFav != BIsFav) return AIsFav;

		// 2) Sort by Package Name.
		const FName AName = A->AssetData.PackageName;
		const FName BName = B->AssetData.PackageName;
		if (AName != BName) return AName.LexicalLess(BName);

		// 3) Sort by Asset Name.
		return A->AssetData.AssetName.LexicalLess(B->AssetData.AssetName);
	});
}

bool StpLevelSelectorWidget::IsSelectedItem(const TSharedPtr<FLevelSelectorItem>& Item) const
{
	return SelectedLevel.IsValid() && SelectedLevel == Item;
}

FGameplayTag StpLevelSelectorWidget::GetItemTag(const TSharedPtr<FLevelSelectorItem>& Item) const
{
	if (!Item.IsValid()) return FGameplayTag::EmptyTag;

	const UTpLevelSelectorSettings* Settings = GetDefault<UTpLevelSelectorSettings>();
	if (!Settings) return FGameplayTag::EmptyTag;

	if (const FGameplayTag* Found = Settings->LevelTags.Find(Item->SoftPath.GetAssetPath()))
	{
		return *Found;
	}
	return FGameplayTag::EmptyTag;
}

void StpLevelSelectorWidget::ApplyFilters()
{
	const FString Search = SearchTextFilter.ToString();
	const bool bHasSearch = !Search.IsEmpty();

	AvailableLevels.Reset(AllLevels.Num() + 1);
	if (SelectedLevel.IsValid())
	{
		AvailableLevels.Add(SelectedLevel);
	}

	const bool bHasTagFilter = SelectedFilterTag.IsValid();

	AvailableLevels.Reserve(AllLevels.Num() + (SelectedLevel.IsValid() ? 1 : 0));
	for (const TSharedPtr<FLevelSelectorItem>& Item : AllLevels)
	{
		if (!Item.IsValid()) continue;
		
		// Tag filter first.
		if (bHasTagFilter && GetItemTag(Item) != SelectedFilterTag) continue;

		// Search filter.
		if (bHasSearch && !Item->DisplayName.Contains(Search, ESearchCase::IgnoreCase, ESearchDir::FromStart)) continue;

		AvailableLevels.Add(Item);
	}

	if (LevelComboBox.IsValid())
	{
		LevelComboBox->RefreshOptions();
	}
}

TSharedRef<SWidget> StpLevelSelectorWidget::OnGenerateWidgetForComboBox(TSharedPtr<FLevelSelectorItem> Item)
{
	return CreateLevelItemWidget(Item);
}

TSharedRef<SWidget> StpLevelSelectorWidget::CreateLevelItemWidget(TSharedPtr<FLevelSelectorItem>& Item)
{
	if (!Item.IsValid())
	{
		return SNew(STextBlock).Text(FText::FromString("Invalid Level"));
	}

	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		[
			SNew(SBox)
			.WidthOverride(24)
			.HeightOverride(24)
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			.Padding(0.0f, 2.0f)
			[
				SNew(SImage)
				.Image(DefaultLevelIcon)
			]
		]
		+ SHorizontalBox::Slot()
		.FillWidth(1.0f)
		.VAlign(VAlign_Center)
		.Padding(4.0f, 2.0f)
		[
			SNew(STextBlock)
			.Text(FText::FromString(Item->DisplayName))
			.Font(FAppStyle::GetFontStyle("PropertyWindow.NormalFont"))
			.MinDesiredWidth(200)
			.Clipping(EWidgetClipping::ClipToBounds)
		];
}