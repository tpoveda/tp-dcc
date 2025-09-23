#include "DebugHelpers.h"
#include "AssetActions/QuickAssetAction.h"


void UQuickAssetAction::TestFunc()
{
	Print(TEXT("Hello World"), FColor::Cyan);
	PrintLog(TEXT("Hello World"));
}
