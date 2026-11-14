#pragma once

#include "openxr/openxr.h"

#ifndef XR_EXT_system_extensions
#define XR_EXT_system_extensions 1
#define XR_EXT_system_extensions_SPEC_VERSION 1
#define XR_EXT_SYSTEM_EXTENSIONS_EXTENSION_NAME "XR_EXT_system_extensions"

#define XR_OBJECT_TYPE_ACTIVE_SYSTEM_EXT ((XrObjectType)1000093000)
#define XR_TYPE_ACTIVE_SYSTEM_CREATE_INFO_EXT ((XrStructureType)1000093000)
#define XR_TYPE_SESSION_ACTIVE_SYSTEM_INFO_EXT ((XrStructureType)1000093001)
#define XR_ERROR_ACTIVE_SYSTEM_LOST_EXT ((XrResult)-1000093000)
#define XR_ACTIVE_SYSTEM_LOSS_PENDING_EXT ((XrResult)1000093000)

XR_DEFINE_HANDLE(XrActiveSystemEXT)

typedef struct XrActiveSystemCreateInfoEXT
{
	XrStructureType type;
	const void* next;
	XrSystemId systemId;
	uint32_t enabledExtensionCount;
	const char* const* enabledExtensionNames;
} XrActiveSystemCreateInfoEXT;

typedef struct XrSessionActiveSystemInfoEXT
{
	XrStructureType type;
	const void* next;
	XrActiveSystemEXT activeSystem;
} XrSessionActiveSystemInfoEXT;

typedef XrResult(XRAPI_PTR* PFN_xrCreateActiveSystemEXT)(
	XrInstance instance,
	const XrActiveSystemCreateInfoEXT* createInfo,
	XrActiveSystemEXT* activeSystem);

typedef XrResult(XRAPI_PTR* PFN_xrDestroyActiveSystemEXT)(
	XrActiveSystemEXT activeSystem);

typedef XrResult(XRAPI_PTR* PFN_xrEnumerateSystemExtensionPropertiesEXT)(
	XrInstance instance,
	XrSystemId systemId,
	uint32_t propertyCapacityInput,
	uint32_t* propertyCountOutput,
	XrExtensionProperties* properties);
#endif

#ifndef XR_BD_eye_tracker
#define XR_BD_eye_tracker 1
#define XR_BD_eye_tracker_SPEC_VERSION 1
#define XR_BD_EYE_TRACKER_EXTENSION_NAME "XR_BD_eye_tracker"

#define XR_OBJECT_TYPE_EYE_TRACKER_BD ((XrObjectType)1000399000)
#define XR_TYPE_EYE_TRACKER_CREATE_INFO_BD ((XrStructureType)1000399001)
#define XR_TYPE_EYE_TRACKER_DATA_INFO_BD ((XrStructureType)1000399002)
#define XR_TYPE_EYE_TRACKER_DATA_BD ((XrStructureType)1000399003)
#define XR_TYPE_EYE_DATA_BD ((XrStructureType)1000399004)
#define XR_TYPE_EYE_TRACKER_GAZE_INFO_BD ((XrStructureType)1000399005)
#define XR_TYPE_EYE_TRACKER_GAZE_BD ((XrStructureType)1000399006)
#define XR_TYPE_EYE_GAZE_BD ((XrStructureType)1000399007)

typedef XrFlags64 XrEyeTrackerFlagsBD;

typedef enum XrEyeTrackerFlagBitsBD
{
	XR_EYE_TRACKER_LEFT_BIT_BD = 0x00000001,
	XR_EYE_TRACKER_RIGHT_BIT_BD = 0x00000002
} XrEyeTrackerFlagBitsBD;

XR_DEFINE_HANDLE(XrEyeTrackerBD)

typedef struct XrEyeTrackerCreateInfoBD
{
	XrStructureType type;
	const void* next;
} XrEyeTrackerCreateInfoBD;

typedef struct XrEyeDataBD
{
	XrStructureType type;
	void* next;
	XrBool32 openness;
} XrEyeDataBD;

typedef struct XrEyeGazeBD
{
	XrStructureType type;
	void* next;
	XrBool32 isValid;
	XrPosef pose;
} XrEyeGazeBD;

typedef struct XrEyeTrackerDataInfoBD
{
	XrStructureType type;
	const void* next;
} XrEyeTrackerDataInfoBD;

typedef struct XrEyeTrackerGazeInfoBD
{
	XrStructureType type;
	const void* next;
	XrEyeTrackerFlagsBD flags;
	XrTime time;
	XrSpace baseSpace;
} XrEyeTrackerGazeInfoBD;

typedef struct XrEyeTrackerDataBD
{
	XrStructureType type;
	void* next;
	XrEyeDataBD leftEyeData;
	XrEyeDataBD rightEyeData;
} XrEyeTrackerDataBD;

typedef struct XrEyeTrackerGazeBD
{
	XrStructureType type;
	void* next;
	XrEyeGazeBD leftEyeGaze;
	XrEyeGazeBD rightEyeGaze;
} XrEyeTrackerGazeBD;

typedef XrResult(XRAPI_PTR* PFN_xrCreateEyeTrackerBD)(
	XrSession session,
	const XrEyeTrackerCreateInfoBD* createInfo,
	XrEyeTrackerBD* tracker);

typedef XrResult(XRAPI_PTR* PFN_xrDestroyEyeTrackerBD)(
	XrEyeTrackerBD tracker);

typedef XrResult(XRAPI_PTR* PFN_xrGetEyeDataBD)(
	XrEyeTrackerBD tracker,
	const XrEyeTrackerDataInfoBD* info,
	XrEyeTrackerDataBD* eyeTrackerData);

typedef XrResult(XRAPI_PTR* PFN_xrGetEyeGazeBD)(
	XrEyeTrackerBD tracker,
	const XrEyeTrackerGazeInfoBD* info,
	XrEyeTrackerGazeBD* gaze);
#endif
