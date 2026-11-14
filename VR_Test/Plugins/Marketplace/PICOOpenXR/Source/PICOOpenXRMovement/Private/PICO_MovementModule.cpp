// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_MovementModule.h"
#include "PICO_EyeTrackingDebugActor.h"

#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"

DEFINE_LOG_CATEGORY(PICOOpenXRMovement);

static TAutoConsoleVariable<int32> CVarPICOAutoSpawnEyeTrackingDebugActor(
    TEXT("pico.OpenXRMovement.AutoSpawnEyeTrackingDebugActor"),
    0,
    TEXT("0: Do not auto-spawn APICOEyeTrackingDebugActor (default)\n")
    TEXT("1: Auto-spawn APICOEyeTrackingDebugActor in PIE/Game worlds for eye tracking debugging\n"),
    ECVF_Default);

void FPICOOpenXRMovementModule::StartupModule()
{
    MovementExtension.Register();
    OnWorldTickStartDelegateHandle = FWorldDelegates::OnWorldTickStart.AddRaw(this, &FPICOOpenXRMovementModule::OnWorldTickStart);
}

void FPICOOpenXRMovementModule::ShutdownModule()
{
    if (OnWorldTickStartDelegateHandle.IsValid())
    {
        FWorldDelegates::OnWorldTickStart.Remove(OnWorldTickStartDelegateHandle);
        OnWorldTickStartDelegateHandle.Reset();
    }

    MovementExtension.Unregister();
}

TSharedPtr<ILiveLinkSource> FPICOOpenXRMovementModule::GetLiveLinkSource()
{
    if (!MovementSource.IsValid())
    {
        AddLiveLinkSource();
    }
    return MovementSource;
}

bool FPICOOpenXRMovementModule::IsLiveLinkSourceValid() const
{
    return MovementSource.IsValid();
}

void FPICOOpenXRMovementModule::AddLiveLinkSource()
{
    if (!MovementSource.IsValid())
    {
        MovementSource = MakeShared<PICOLiveLink::LiveLinkSource>();
    }
}

void FPICOOpenXRMovementModule::RemoveLiveLinkSource()
{
    MovementSource.Reset();
}

void FPICOOpenXRMovementModule::OnWorldTickStart(UWorld* InWorld, ELevelTick TickType, float DeltaTime)
{
    if (!IsInGameThread() || InWorld == nullptr || GEngine == nullptr)
    {
        return;
    }

    if (CVarPICOAutoSpawnEyeTrackingDebugActor.GetValueOnGameThread() == 0)
    {
        return;
    }

    const FWorldContext* Context = GEngine->GetWorldContextFromWorld(InWorld);
    if (Context == nullptr || (Context->WorldType != EWorldType::PIE && Context->WorldType != EWorldType::Game) || Context->World() == nullptr)
    {
        return;
    }

    TActorIterator<APICOEyeTrackingDebugActor> ExistingDebugActor(InWorld);
    if (ExistingDebugActor)
    {
        return;
    }

    FActorSpawnParameters SpawnInfo;
    SpawnInfo.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    SpawnInfo.bNoFail = true;
    SpawnInfo.ObjectFlags = RF_Transient;

    APICOEyeTrackingDebugActor* DebugActor = InWorld->SpawnActor<APICOEyeTrackingDebugActor>(SpawnInfo);
    if (DebugActor != nullptr)
    {
        DebugActor->SetActorEnableCollision(false);
        UE_LOG(PICOOpenXRMovement, Log, TEXT("Spawned APICOEyeTrackingDebugActor automatically for eye tracking debug."));
    }
}

IMPLEMENT_MODULE(FPICOOpenXRMovementModule, PICOOpenXRMovement)
