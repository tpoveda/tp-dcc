#pragma once

#include "GameplayTagContainer.h"
#include "AssetRegistry/AssetData.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Input/SComboBox.h"


struct FLevelSelectorItem
{
	FString DisplayName;
	FString PackagePath;
	FSoftObjectPath SoftPath;
	FAssetData AssetData;

	explicit FLevelSelectorItem(const FAssetData& AssetData);

	static TSharedRef<FLevelSelectorItem> Create(const FAssetData& AssetData)
	{
		return MakeShareable(new FLevelSelectorItem(AssetData));
	}
};


class TPLEVELSELECTOR_API StpLevelSelectorWidget : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(StpLevelSelectorWidget){}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	void PopulateLevels();
	void SortLevels();
	
	TArray<TSharedPtr<FLevelSelectorItem>> AllLevels;
	TArray<TSharedPtr<FLevelSelectorItem>> AvailableLevels;
	TSharedPtr<FLevelSelectorItem> SelectedLevel;
	
	TSharedPtr<SComboBox<TSharedPtr<FLevelSelectorItem>>> LevelComboBox;
	TSharedPtr<SBox> ComboBoxContentContainer;
	const FSlateBrush* DefaultLevelIcon{nullptr};
	const FSlateBrush* RefreshIconBrush{nullptr};

	TSharedRef<SWidget> CreateLevelItemWidget(TSharedPtr<FLevelSelectorItem>& Item);
	bool IsSelectedItem(const TSharedPtr<FLevelSelectorItem>& Item) const;
	FGameplayTag GetItemTag(const TSharedPtr<FLevelSelectorItem>& Item) const;
	void RefreshSelection(const FString& MapPath, bool bStrict = true);
	TSharedRef<SWidget> OnGenerateWidgetForComboBox(TSharedPtr<FLevelSelectorItem> Item);
	FReply OnRefreshButtonClicked();

	void ApplyFilters();
	FText SearchTextFilter;
	FGameplayTag SelectedFilterTag;
};
