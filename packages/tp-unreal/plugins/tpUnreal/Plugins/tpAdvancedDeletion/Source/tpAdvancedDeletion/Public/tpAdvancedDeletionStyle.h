#pragma once

#include "Styling/SlateStyle.h"


class FtpAdvancedDeletionStyle
{
public:
	static void Initialize();
	static void Shutdown();

	static FName GetStyleSetName();

private:
	static FName StyleSetName;

	static TSharedRef<FSlateStyleSet> CreateSlateStyleSet();
	static TSharedPtr<FSlateStyleSet> StyleSet;
};
