#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"


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
	
	TArray<TSharedPtr<FAssetData>> AssetsData;
};
