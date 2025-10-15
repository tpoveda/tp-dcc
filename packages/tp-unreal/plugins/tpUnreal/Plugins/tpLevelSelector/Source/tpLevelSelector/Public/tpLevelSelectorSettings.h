#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Engine/DeveloperSettings.h"
#include "TpLevelSelectorSettings.generated.h"

UCLASS(Config=Editor, DefaultConfig)
class TPLEVELSELECTOR_API UTpLevelSelectorSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UTpLevelSelectorSettings();

	UPROPERTY(Config, EditAnywhere, Category = "Level Selector")
	TSet<FSoftObjectPath> FavoriteLevels;

	UPROPERTY(Config, EditAnywhere, Category = "Level Selector")
	TMap<FTopLevelAssetPath, FGameplayTag> LevelTags;
};
