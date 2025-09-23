#pragma once

inline void Print(const FString& Message, const FColor& Color)
{
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 8.f, Color, Message);
	}
}

inline void PrintLog(const FString& Message)
{
	UE_LOG(LogTemp, Warning, TEXT("%s"), *Message);
}