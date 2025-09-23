#pragma once

#include "Engine/Engine.h"
#include "Framework/Notifications/NotificationManager.h"
#include "Misc/MessageDialog.h"
#include "Widgets/Notifications/SNotificationList.h"

/**
 * @brief Outputs a message to the standard output or a designated device.
 *
 * @param Message The text string to be printed.
 * @param Color The color to display the message in.
 */
inline void Print(const FString& Message, const FColor& Color)
{
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 8.f, Color, Message);
	}
}

/**
 * @brief Logs a warning message to the output log.
 *
 * @param Message The text string to be logged.
 */
inline void PrintLog(const FString& Message)
{
	UE_LOG(LogTemp, Warning, TEXT("%s"), *Message);
}

/**
 * @brief Displays a message dialog with the specified message type and content.
 *
 * @param MessageType The type of message dialog to display.
 * @param Message The message text to be shown in the dialog.
 * @param bShowMessageAsWarning Determines whether to categorize the message as a warning.
 * @return The type of action or response selected by the user from the dialog.
 */
inline EAppReturnType::Type ShowMessageDialog(EAppMsgType::Type MessageType, const FString& Message, const bool bShowMessageAsWarning = true)
{
	if (bShowMessageAsWarning)
	{
		return FMessageDialog::Open(MessageType, FText::FromString(Message), FText::FromString("Warning"));
	}
	return FMessageDialog::Open(EAppMsgType::Ok, FText::FromString(Message));
}

/**
 * @brief Displays a notification message with a large font and a fade-out effect.
 *
 * @param Message The message text to be shown in the notification.
 */
inline void ShowNotifyInfo(const FString& Message)
{
	FNotificationInfo NotifyInfo(FText::FromString(Message));
	NotifyInfo.bUseLargeFont = true;
	NotifyInfo.FadeOutDuration = 7.0f;
	FSlateNotificationManager::Get().AddNotification(NotifyInfo);
}