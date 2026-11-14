// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Exporters/Exporter.h"
#include "PICO_HandGestureSemanticRecognizerExporter.generated.h"

UCLASS()
class PICOOPENXREDITOR_API UPICOOpenXRHandGestureSemanticRecognizerExporter : public UExporter
{
	GENERATED_BODY()

public:
	UPICOOpenXRHandGestureSemanticRecognizerExporter(const FObjectInitializer& ObjectInitializer);

	virtual bool SupportsObject(UObject* Object) const override;
	virtual bool ExportText(const FExportObjectInnerContext* Context, UObject* Object, const TCHAR* Type, FOutputDevice& Ar, FFeedbackContext* Warn, uint32 PortFlags = 0) override;
};
