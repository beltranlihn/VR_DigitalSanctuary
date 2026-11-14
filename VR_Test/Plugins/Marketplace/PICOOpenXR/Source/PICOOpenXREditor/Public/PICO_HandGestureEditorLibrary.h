// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "PICO_HandGestureEditorLibrary.generated.h"

class UPoseAsset;
class UPICOHandGestureRecognizerAsset;
class UPICOHandGestureSemanticRecognizerAsset;

UCLASS()
class PICOOPENXREDITOR_API UPICOHandGestureEditorLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "PICO|HandGesture|Editor")
	static bool ExportPoseAssetPoseToJson(UPoseAsset* PoseAsset, FName PoseName, const FString& OutputFilename, FString& OutJson, FString& OutError);

	UFUNCTION(BlueprintCallable, Category = "PICO|HandGesture|Editor")
	static bool ExportRecognizerAssetToJson(UPICOHandGestureRecognizerAsset* RecognizerAsset, const FString& OutputFilename, FString& OutJson, FString& OutError);

        UFUNCTION(BlueprintCallable, Category = "PICO|HandGesture|Editor")
        static bool ExportSemanticRecognizerAssetToJson(UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, const FString& OutputFilename, FString& OutJson, FString& OutError);

        static bool ImportOpenXRHandPoseJsonFileToPoseAsset(const FString& JsonFilename, UPoseAsset* PoseAsset, FString& OutError);
        static bool ImportOpenXRHandPoseJsonToPoseAsset(const FString& JsonString, UPoseAsset* PoseAsset, FString& OutError);
	static bool ImportRecognizerJsonFileToRecognizerAsset(const FString& JsonFilename, UPICOHandGestureRecognizerAsset* RecognizerAsset, FString& OutError);
	static bool ImportRecognizerJsonToRecognizerAsset(const FString& JsonString, UPICOHandGestureRecognizerAsset* RecognizerAsset, FString& OutError);
        static bool ImportSemanticRecognizerJsonFileToRecognizerAsset(const FString& JsonFilename, UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, FString& OutError);
        static bool ImportSemanticRecognizerJsonToRecognizerAsset(const FString& JsonString, UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, FString& OutError);
        static bool InitializeSemanticRecognizerFromPoseAsset(UPoseAsset* PoseAsset, UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, FString& OutError);
};
