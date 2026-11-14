// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Exporters/Exporter.h"
#include "PICO_HandGestureRecognizerExporter.generated.h"

UCLASS()
class PICOOPENXREDITOR_API UPICOOpenXRHandGestureRecognizerExporter : public UExporter
{
	GENERATED_BODY()

public:
	UPICOOpenXRHandGestureRecognizerExporter(const FObjectInitializer& ObjectInitializer);

	virtual bool SupportsObject(UObject* Object) const override;
	virtual bool ExportText(const FExportObjectInnerContext* Context, UObject* Object, const TCHAR* Type, FOutputDevice& Ar, FFeedbackContext* Warn, uint32 PortFlags = 0) override;
};
