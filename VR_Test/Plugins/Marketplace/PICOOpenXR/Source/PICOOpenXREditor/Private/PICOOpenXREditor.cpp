// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_HandGestureEditorLibrary.h"
#include "PICO_HandGestureRecognizerAsset.h"
#include "PICO_HandGestureSemanticRecognizerAsset.h"
#include "PICOOpenXRRuntimeSettings.h"
#include "PICOHapticAssetFactory.h"
#include "PICOHapticAssetThumbnailRenderer.h"
#include "PICOHapticAsset.h"
#include "Animation/PoseAsset.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "ContentBrowserModule.h"
#include "ContentBrowserMenuContexts.h"
#include "DesktopPlatformModule.h"
#include "Framework/Notifications/NotificationManager.h"
#include "HAL/FileManager.h"
#include "IContentBrowserSingleton.h"
#include "Modules/ModuleInterface.h"
#include "ISettingsModule.h"
#include "Misc/MessageDialog.h"
#include "Modules/ModuleManager.h"
#include "Styling/AppStyle.h"
#include "ToolMenus.h"
#include "UObject/Package.h"
#include "PropertyEditorModule.h"
#include "OpenXRHMDSettings.h"
#include "Engine/RendererSettings.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "ThumbnailRendering/ThumbnailManager.h"
#include "Widgets/Notifications/SNotificationList.h"

#define LOCTEXT_NAMESPACE "FPICOOpenXREditorModule"

namespace MenuExtension_PoseAsset
{
	static UPoseAsset* GetPoseAssetFromContext(const FToolMenuContext& InContext)
	{
		if (UContentBrowserAssetContextMenuContext::GetNumAssetsSelected(InContext) != 1)
		{
			return nullptr;
		}

		const UContentBrowserAssetContextMenuContext* Context = UContentBrowserAssetContextMenuContext::FindContextWithAssets(InContext);
		if (!Context)
		{
			return nullptr;
		}

		const TArray<UPoseAsset*> PoseAssets = Context->LoadSelectedObjects<UPoseAsset>();
		return PoseAssets.Num() == 1 ? PoseAssets[0] : nullptr;
	}

	static bool CanExportPoseJson(const FToolMenuContext& InContext)
	{
		return GetPoseAssetFromContext(InContext) != nullptr;
	}

	static bool CanCreateRecognizer(const FToolMenuContext& InContext)
	{
		return GetPoseAssetFromContext(InContext) != nullptr;
	}

	static bool CanCreateSemanticRecognizer(const FToolMenuContext& InContext)
	{
		return GetPoseAssetFromContext(InContext) != nullptr;
	}

	static void ShowNotification(const FText& Message, const SNotificationItem::ECompletionState CompletionState)
	{
		FNotificationInfo Info(Message);
		Info.ExpireDuration = 5.0f;

		if (TSharedPtr<SNotificationItem> Notification = FSlateNotificationManager::Get().AddNotification(Info))
		{
			Notification->SetCompletionState(CompletionState);
		}
	}

	static FName ResolveDefaultPoseName(const UPoseAsset* PoseAsset)
	{
		if (!PoseAsset || PoseAsset->GetNumPoses() <= 0)
		{
			return NAME_None;
		}

		return PoseAsset->GetPoseIndexByName(TEXT("Pose_0")) != INDEX_NONE
			? FName(TEXT("Pose_0"))
			: PoseAsset->GetPoseNameByIndex(0);
	}

	static void FillDefaultRecognizerRules(UPICOHandGestureRecognizerAsset* RecognizerAsset)
	{
		if (!RecognizerAsset)
		{
			return;
		}

		RecognizerAsset->JointRules.Reset();
		RecognizerAsset->JointRules.Reserve(EHandKeypointCount);

		for (int32 KeypointIndex = 0; KeypointIndex < EHandKeypointCount; ++KeypointIndex)
		{
			const EHandKeypoint Keypoint = static_cast<EHandKeypoint>(KeypointIndex);

			FPICOHandGestureJointMatchRule& Rule = RecognizerAsset->JointRules.AddDefaulted_GetRef();
			Rule.Joint = Keypoint;
			Rule.bEnabled = Keypoint != EHandKeypoint::Palm && Keypoint != EHandKeypoint::Wrist;
			Rule.bMatchRotation = true;
			Rule.bMatchPosition = false;
			Rule.Weight = 1.0f;
			Rule.AngularToleranceDeg = 35.0f;
			Rule.PositionToleranceCm = 5.0f;
		}
	}

	static void ExecuteCreateRecognizer(const FToolMenuContext& InContext)
	{
		UPoseAsset* PoseAsset = GetPoseAssetFromContext(InContext);
		if (!PoseAsset)
		{
			ShowNotification(LOCTEXT("CreateRecognizerNoSelection", "Select exactly one PoseAsset."), SNotificationItem::CS_Fail);
			return;
		}

		const UPackage* PosePackage = PoseAsset->GetOutermost();
		const FString PosePackageName = PosePackage ? PosePackage->GetName() : FString();
		const FString PackagePath = FPackageName::GetLongPackagePath(PosePackageName);
		if (PackagePath.IsEmpty())
		{
			ShowNotification(LOCTEXT("CreateRecognizerInvalidPackage", "Could not resolve PoseAsset package path."), SNotificationItem::CS_Fail);
			return;
		}

		FString UniquePackageName;
		FString UniqueAssetName;
		FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
		AssetToolsModule.Get().CreateUniqueAssetName(
			PackagePath / FString::Printf(TEXT("%s_Recognizer"), *PoseAsset->GetName()),
			FString(),
			UniquePackageName,
			UniqueAssetName);

		UPackage* RecognizerPackage = CreatePackage(*UniquePackageName);
		if (!RecognizerPackage)
		{
			ShowNotification(LOCTEXT("CreateRecognizerPackageFailed", "Failed to create recognizer package."), SNotificationItem::CS_Fail);
			return;
		}

		UPICOHandGestureRecognizerAsset* RecognizerAsset = NewObject<UPICOHandGestureRecognizerAsset>(
			RecognizerPackage,
			UPICOHandGestureRecognizerAsset::StaticClass(),
			*UniqueAssetName,
			RF_Public | RF_Standalone | RF_Transactional);
		if (!RecognizerAsset)
		{
			ShowNotification(LOCTEXT("CreateRecognizerAssetFailed", "Failed to create recognizer asset."), SNotificationItem::CS_Fail);
			return;
		}

		RecognizerAsset->TargetPoseAsset = PoseAsset;
		RecognizerAsset->PoseName = ResolveDefaultPoseName(PoseAsset);
		RecognizerAsset->bUseDefaultFullPoseRulesWhenEmpty = false;
		RecognizerAsset->MatchThreshold = 0.75f;
		FillDefaultRecognizerRules(RecognizerAsset);

		FAssetRegistryModule::AssetCreated(RecognizerAsset);
		RecognizerPackage->MarkPackageDirty();
		RecognizerAsset->PostEditChange();

		FContentBrowserModule& ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
		TArray<UObject*> AssetsToSync;
		AssetsToSync.Add(RecognizerAsset);
		ContentBrowserModule.Get().SyncBrowserToAssets(AssetsToSync);

		ShowNotification(
			FText::Format(
				LOCTEXT("CreateRecognizerSucceeded", "Created recognizer {0}."),
				FText::FromString(UniqueAssetName)),
			SNotificationItem::CS_Success);
	}

	static void ExecuteCreateSemanticRecognizer(const FToolMenuContext& InContext)
	{
		UPoseAsset* PoseAsset = GetPoseAssetFromContext(InContext);
		if (!PoseAsset)
		{
			ShowNotification(LOCTEXT("CreateSemanticRecognizerNoSelection", "Select exactly one PoseAsset."), SNotificationItem::CS_Fail);
			return;
		}

		const UPackage* PosePackage = PoseAsset->GetOutermost();
		const FString PosePackageName = PosePackage ? PosePackage->GetName() : FString();
		const FString PackagePath = FPackageName::GetLongPackagePath(PosePackageName);
		if (PackagePath.IsEmpty())
		{
			ShowNotification(LOCTEXT("CreateSemanticRecognizerInvalidPackage", "Could not resolve PoseAsset package path."), SNotificationItem::CS_Fail);
			return;
		}

		FString UniquePackageName;
		FString UniqueAssetName;
		FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
		AssetToolsModule.Get().CreateUniqueAssetName(
			PackagePath / FString::Printf(TEXT("%s_SemanticRecognizer"), *PoseAsset->GetName()),
			FString(),
			UniquePackageName,
			UniqueAssetName);

		UPackage* RecognizerPackage = CreatePackage(*UniquePackageName);
		if (!RecognizerPackage)
		{
			ShowNotification(LOCTEXT("CreateSemanticRecognizerPackageFailed", "Failed to create semantic recognizer package."), SNotificationItem::CS_Fail);
			return;
		}

		UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset = NewObject<UPICOHandGestureSemanticRecognizerAsset>(
			RecognizerPackage,
			UPICOHandGestureSemanticRecognizerAsset::StaticClass(),
			*UniqueAssetName,
			RF_Public | RF_Standalone | RF_Transactional);
		if (!RecognizerAsset)
		{
			ShowNotification(LOCTEXT("CreateSemanticRecognizerAssetFailed", "Failed to create semantic recognizer asset."), SNotificationItem::CS_Fail);
			return;
		}

		FString OutError;
		if (!UPICOHandGestureEditorLibrary::InitializeSemanticRecognizerFromPoseAsset(PoseAsset, RecognizerAsset, OutError))
		{
			ShowNotification(
				FText::Format(LOCTEXT("CreateSemanticRecognizerFailed", "Failed to create semantic recognizer: {0}"), FText::FromString(OutError)),
				SNotificationItem::CS_Fail);
			return;
		}

		FAssetRegistryModule::AssetCreated(RecognizerAsset);
		RecognizerPackage->MarkPackageDirty();
		RecognizerAsset->PostEditChange();

		FContentBrowserModule& ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
		TArray<UObject*> AssetsToSync;
		AssetsToSync.Add(RecognizerAsset);
		ContentBrowserModule.Get().SyncBrowserToAssets(AssetsToSync);

		ShowNotification(
			FText::Format(
				LOCTEXT("CreateSemanticRecognizerSucceeded", "Created semantic recognizer {0}."),
				FText::FromString(UniqueAssetName)),
			SNotificationItem::CS_Success);
	}

	static void ExecuteExportPoseJson(const FToolMenuContext& InContext)
	{
		UPoseAsset* PoseAsset = GetPoseAssetFromContext(InContext);
		if (!PoseAsset)
		{
			ShowNotification(LOCTEXT("ExportPoseJsonNoSelection", "Select exactly one PoseAsset."), SNotificationItem::CS_Fail);
			return;
		}

		const FString DefaultDirectory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Trae"));
		IFileManager::Get().MakeDirectory(*DefaultDirectory, true);

		const FString DefaultFilename = FString::Printf(TEXT("%s.json"), *PoseAsset->GetName());

		IDesktopPlatform* DesktopPlatform = FDesktopPlatformModule::Get();
		if (!DesktopPlatform)
		{
			ShowNotification(LOCTEXT("ExportPoseJsonDesktopPlatformUnavailable", "DesktopPlatform is unavailable."), SNotificationItem::CS_Fail);
			return;
		}

		TArray<FString> OutFilenames;
		const bool bFileChosen = DesktopPlatform->SaveFileDialog(
			nullptr,
			LOCTEXT("ExportPoseJsonDialogTitle", "Export Pose JSON").ToString(),
			DefaultDirectory,
			DefaultFilename,
			TEXT("JSON (*.json)|*.json"),
			0,
			OutFilenames);

		if (!bFileChosen || OutFilenames.Num() != 1)
		{
			return;
		}

		FString OutJson;
		FString OutError;
		if (!UPICOHandGestureEditorLibrary::ExportPoseAssetPoseToJson(PoseAsset, NAME_None, OutFilenames[0], OutJson, OutError))
		{
			ShowNotification(FText::Format(LOCTEXT("ExportPoseJsonFailed", "Failed to export Pose JSON: {0}"), FText::FromString(OutError)), SNotificationItem::CS_Fail);
			return;
		}

		ShowNotification(
			FText::Format(
				LOCTEXT("ExportPoseJsonSucceeded", "Exported Pose JSON for {0}."),
				FText::FromString(PoseAsset->GetName())),
			SNotificationItem::CS_Success);
	}
}

static void EnsureMacMobileMultiViewEnabled()
{
#if PLATFORM_MAC
	const FString MacEnginePath = FConfigCacheIni::NormalizeConfigIniPath(FPaths::Combine(FPaths::ProjectConfigDir(), TEXT("Mac/MacEngine.ini")));

	if (GConfig)
	{
		GConfig->LoadFile(MacEnginePath);

		bool bMobileMultiView = false;
		GConfig->GetBool(TEXT("/Script/Engine.RendererSettings"), TEXT("vr.MobileMultiView"), bMobileMultiView, MacEnginePath);

		if (!bMobileMultiView)
		{
			GConfig->SetBool(TEXT("/Script/Engine.RendererSettings"), TEXT("vr.MobileMultiView"), true, MacEnginePath);
			GConfig->Flush(false, MacEnginePath);
		}

		GConfig->UnloadFile(MacEnginePath);
	}

	if (URendererSettings* RendererSettings = GetMutableDefault<URendererSettings>())
	{
		RendererSettings->bMobileMultiView = true;
	}
#endif
}

class FPICOOpenXREditorModule
: public IModuleInterface
{
	void RegisterMenus()
	{
		FToolMenuOwnerScoped OwnerScoped(this);

		UToolMenu* Menu = UE::ContentBrowser::ExtendToolMenu_AssetContextMenu(UPoseAsset::StaticClass());
		if (!Menu)
		{
			return;
		}

		FToolMenuSection& Section = Menu->FindOrAddSection("GetAssetActions");
		Section.AddDynamicEntry("PICOOpenXRPoseAssetActions", FNewToolMenuSectionDelegate::CreateLambda([](FToolMenuSection& InSection)
		{
			if (const UContentBrowserAssetContextMenuContext* Context = UContentBrowserAssetContextMenuContext::FindContextWithAssets(InSection))
			{
				if (Context->SelectedAssets.Num() > 0 && Context->SelectedAssets[0].AssetClassPath == UPoseAsset::StaticClass()->GetClassPathName())
				{
					FToolUIAction UIAction;
					UIAction.ExecuteAction = FToolMenuExecuteAction::CreateStatic(&MenuExtension_PoseAsset::ExecuteExportPoseJson);
					UIAction.CanExecuteAction = FToolMenuCanExecuteAction::CreateStatic(&MenuExtension_PoseAsset::CanExportPoseJson);
					UIAction.IsActionVisibleDelegate = FToolMenuIsActionButtonVisible::CreateStatic(&MenuExtension_PoseAsset::CanExportPoseJson);

					InSection.AddMenuEntry(
						"PICOOpenXRExportPoseJson",
						LOCTEXT("ExportPoseJsonMenuLabel", "Export Pose JSON..."),
						LOCTEXT("ExportPoseJsonMenuToolTip", "Export Pose_0 local transforms to a JSON file."),
						FSlateIcon(FAppStyle::GetAppStyleSetName(), "ClassIcon.PoseAsset"),
						UIAction);

					FToolUIAction CreateRecognizerAction;
					CreateRecognizerAction.ExecuteAction = FToolMenuExecuteAction::CreateStatic(&MenuExtension_PoseAsset::ExecuteCreateRecognizer);
					CreateRecognizerAction.CanExecuteAction = FToolMenuCanExecuteAction::CreateStatic(&MenuExtension_PoseAsset::CanCreateRecognizer);
					CreateRecognizerAction.IsActionVisibleDelegate = FToolMenuIsActionButtonVisible::CreateStatic(&MenuExtension_PoseAsset::CanCreateRecognizer);

					InSection.AddMenuEntry(
						"PICOOpenXRCreateGestureRecognizer",
						LOCTEXT("CreateRecognizerMenuLabel", "Create PICO Gesture Recognizer"),
						LOCTEXT("CreateRecognizerMenuToolTip", "Create a UPICOHandGestureRecognizerAsset next to this PoseAsset with editable default joint rules."),
						FSlateIcon(FAppStyle::GetAppStyleSetName(), "ClassIcon.DataAsset"),
						CreateRecognizerAction);

					FToolUIAction CreateSemanticRecognizerAction;
					CreateSemanticRecognizerAction.ExecuteAction = FToolMenuExecuteAction::CreateStatic(&MenuExtension_PoseAsset::ExecuteCreateSemanticRecognizer);
					CreateSemanticRecognizerAction.CanExecuteAction = FToolMenuCanExecuteAction::CreateStatic(&MenuExtension_PoseAsset::CanCreateSemanticRecognizer);
					CreateSemanticRecognizerAction.IsActionVisibleDelegate = FToolMenuIsActionButtonVisible::CreateStatic(&MenuExtension_PoseAsset::CanCreateSemanticRecognizer);
					InSection.AddMenuEntry(
						"PICOOpenXRCreateSemanticRecognizer",
						LOCTEXT("CreateSemanticRecognizerMenuLabel", "Create PICO Semantic Recognizer"),
						LOCTEXT("CreateSemanticRecognizerMenuToolTip", "Create a UPICOHandGestureSemanticRecognizerAsset next to this PoseAsset using semantic curl/spread feature rules."),
						FSlateIcon(FAppStyle::GetAppStyleSetName(), "ClassIcon.DataAsset"),
						CreateSemanticRecognizerAction);
				}
			}
		}));
	}

	virtual void StartupModule() override
	{
		EnsureMacMobileMultiViewEnabled();

		ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings");

		if (SettingsModule != nullptr)
		{
			SettingsModule->RegisterSettings("Project", "Plugins", "PICOOpenXR",
				LOCTEXT("RuntimeSettingsName", "PICO OpenXR"),
				LOCTEXT("RuntimeSettingsDescription", "Project settings for PICO OpenXR Extension plugin"),
				GetMutableDefault<UPICOOpenXRRuntimeSettings>()
			);
		}

		UOpenXRHMDSettings* OpenXRHMDSettings = GetMutableDefault<UOpenXRHMDSettings>();
		if (OpenXRHMDSettings)
		{
			OpenXRHMDSettings->bIsFBFoveationEnabled = true;
			OpenXRHMDSettings->UpdateSinglePropertyInConfigFile(OpenXRHMDSettings->GetClass()->FindPropertyByName(GET_MEMBER_NAME_CHECKED(UOpenXRHMDSettings, bIsFBFoveationEnabled)), OpenXRHMDSettings->GetDefaultConfigFilename());
		}

		UThumbnailManager::Get().RegisterCustomRenderer(UPICOHapticAsset::StaticClass(), UPICOHapticAssetThumbnailRenderer::StaticClass());
		UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FPICOOpenXREditorModule::RegisterMenus));
	}

	virtual void ShutdownModule() override
	{
		UToolMenus::UnRegisterStartupCallback(this);
		UToolMenus::UnregisterOwner(this);

		ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings");

		if (SettingsModule != nullptr)
		{
			SettingsModule->UnregisterSettings("Project", "Plugins", "PICOOpenXR");
		}

		if (UObjectInitialized())
		{
			UThumbnailManager::Get().UnregisterCustomRenderer(UPICOHapticAsset::StaticClass());
		}
	}
};

IMPLEMENT_MODULE(FPICOOpenXREditorModule, PICOOpenXREditor);

#undef LOCTEXT_NAMESPACE
