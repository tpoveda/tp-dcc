#include <maya/MPxLocatorNode.h>
#include <maya/MString.h>
#include <maya/MTypeId.h>
#include <maya/MPlug.h>
#include <maya/MVector.h>
#include <maya/MDataBlock.h>
#include <maya/MDataHandle.h>
#include <maya/MColor.h>
#include <maya/M3dView.h>
#include <maya/MFnPlugin.h>
#include <maya/MDistance.h>
#include <maya/MFnUnitAttribute.h>

// Viewport 2.0 includes
#include <maya/MDrawRegistry.h>
#include <maya/MPxDrawOverride.h>
#include <maya/MUserData.h>
#include <maya/MDrawContext.h>
#include <maya/MHWGeometryUtilities.h>
#include <maya/MPointArray.h>

#include <assert.h>

//---------------------------------------------------------------------------
//---------------------------------------------------------------------------
// Node implementation with standard viewport draw
//---------------------------------------------------------------------------
//---------------------------------------------------------------------------

class tpAnnotation : public MPxLocatorNode
{
public:
	tpAnnotation();
	virtual ~tpAnnotation();

	virtual MStatus compute(const MPlug& plug, MDataBlock& data);

	virtual void draw(M3dView& view, const MDagPath& path, M3dView::DisplayStyle style, M3dView::DisplayStatus status);

	virtual bool isBounded() const;
	virtual MBoundingBox boundingBox() const;

	static  void* creator();
	static  MStatus initialize();

	static  MObject size;         // The size of the foot

public:
	static	MTypeId id;
	static	MString drawDbClassification;
	static	MString	drawRegistrantId;
};

MObject tpAnnotation::size;
MTypeId tpAnnotation::id(0x80007);
MString	tpAnnotation::drawDbClassification("drawdb/geometry/tpAnnotation");
MString	tpAnnotation::drawRegistrantId("tpAnnotationPlugin");

tpAnnotation::tpAnnotation() 
{
}

tpAnnotation::~tpAnnotation() 
{

}

MStatus tpAnnotation::compute(const MPlug& /*plug*/, MDataBlock& /*data*/)
{
	return MS::kUnknownParameter;
}

// called by legacy default viewport
void tpAnnotation::draw(M3dView& view, const MDagPath& /*path*/, M3dView::DisplayStyle style, M3dView::DisplayStatus status)
{
	// Get the size
	//
	MObject thisNode = thisMObject();
	MPlug plug(thisNode, size);
	MDistance sizeVal;
	plug.getValue(sizeVal);

	float multiplier = (float)sizeVal.asCentimeters();

	// Draw the name of the annotation
	view.setDrawColor(MColor(0.1f, 0.8f, 0.8f, 1.0f));
	view.drawText(MString("tpAnnotation"), MPoint(0.0, 0.0, 0.0), M3dView::kCenter);
}

bool tpAnnotation::isBounded() const
{
	return true;
}

MBoundingBox tpAnnotation::boundingBox() const
{
	// Get the size
	//
	MObject thisNode = thisMObject();
	MPlug plug(thisNode, size);
	MDistance sizeVal;
	plug.getValue(sizeVal);

	double multiplier = sizeVal.asCentimeters();

	MPoint corner1(-0.17, 0.0, -0.7);
	MPoint corner2(0.17, 0.0, 0.3);

	corner1 = corner1 * multiplier;
	corner2 = corner2 * multiplier;

	return MBoundingBox(corner1, corner2);
}

void* tpAnnotation::creator()
{
	return new tpAnnotation();
}

//---------------------------------------------------------------------------
//---------------------------------------------------------------------------
// Viewport 2.0 override implementation
//---------------------------------------------------------------------------
//---------------------------------------------------------------------------

class tpAnnotationData : public MUserData
{
public:
	tpAnnotationData() : MUserData(false) {} // don't delete after draw
	virtual ~tpAnnotationData() {}

	MColor fColor;
};

class tpAnnotationDrawOverride : public MHWRender::MPxDrawOverride
{
public:
	static MHWRender::MPxDrawOverride* Creator(const MObject& obj) { return new tpAnnotationDrawOverride(obj); }
	virtual ~tpAnnotationDrawOverride();
	virtual MHWRender::DrawAPI supportedDrawAPIs() const;
	virtual bool isBounded(const MDagPath& objPath, const MDagPath& cameraPath) const;
	virtual MBoundingBox boundingBox(const MDagPath& objPath, const MDagPath& cameraPath) const;
	virtual MUserData* prepareForDraw(const MDagPath& objPath, const MDagPath& cameraPath, const MHWRender::MFrameContext& frameContext, MUserData* oldData);
	virtual bool hasUIDrawables() const { return true; }
	virtual void addUIDrawables(const MDagPath& objPath, MHWRender::MUIDrawManager& drawManager, const MHWRender::MFrameContext& frameContext, const MUserData* data);
	static void draw(const MHWRender::MDrawContext& context, const MUserData* data) {};

private:
	tpAnnotationDrawOverride(const MObject& obj);
	float getMultiplier(const MDagPath& objPath) const;
};

tpAnnotationDrawOverride::tpAnnotationDrawOverride(const MObject& obj)
	: MHWRender::MPxDrawOverride(obj, tpAnnotationDrawOverride::draw)
{
}

tpAnnotationDrawOverride::~tpAnnotationDrawOverride()
{
}

MHWRender::DrawAPI tpAnnotationDrawOverride::supportedDrawAPIs() const
{
	// this plugin supports both GL and DX
	return (MHWRender::kOpenGL | MHWRender::kDirectX11 | MHWRender::kOpenGLCoreProfile);
}

float tpAnnotationDrawOverride::getMultiplier(const MDagPath& objPath) const
{
	// Retrieve value of the size attribute from the node
	MStatus status;
	MObject annotationNode = objPath.node(&status);
	if (status)
	{
		MPlug plug(annotationNode, tpAnnotation::size);
		if (!plug.isNull())
		{
			MDistance sizeVal;
			if (plug.getValue(sizeVal))
			{
				return (float)sizeVal.asCentimeters();
			}
		}
	}

	return 1.0f;
}

bool tpAnnotationDrawOverride::isBounded(const MDagPath& /*objPath*/,
	const MDagPath& /*cameraPath*/) const
{
	return true;
}

MBoundingBox tpAnnotationDrawOverride::boundingBox(
	const MDagPath& objPath,
	const MDagPath& cameraPath) const
{
	MPoint corner1(-0.17, 0.0, -0.7);
	MPoint corner2(0.17, 0.0, 0.3);

	float multiplier = getMultiplier(objPath);
	corner1 = corner1 * multiplier;
	corner2 = corner2 * multiplier;

	return MBoundingBox(corner1, corner2);
}

// Called by Maya each time the object needs to be drawn.
MUserData* tpAnnotationDrawOverride::prepareForDraw(const MDagPath& objPath, const MDagPath& cameraPath, const MHWRender::MFrameContext& frameContext, MUserData* oldData)
{
	// Any data needed from the Maya dependency graph must be retrieved and cached in this stage.
	// There is one cache data for each drawable instance, if it is not desirable to allow Maya to handle data
	// caching, simply return null in this method and ignore user data parameter in draw callback method.
	// e.g. in this sample, we compute and cache the data for usage later when we create the 
	// MUIDrawManager to draw annotation in method addUIDrawables().
	tpAnnotationData* data = dynamic_cast<tpAnnotationData*>(oldData);
	if (!data)
	{
		data = new tpAnnotationData();
	}

	float fMultiplier = getMultiplier(objPath);

	// get correct color based on the state of object, e.g. active or dormant
	data->fColor = MHWRender::MGeometryUtilities::wireframeColor(objPath);

	return data;
}

// addUIDrawables() provides access to the MUIDrawManager, which can be used
// to queue up operations for drawing simple UI elements such as lines, circles and
// text. To enable addUIDrawables(), override hasUIDrawables() and make it return true.
void tpAnnotationDrawOverride::addUIDrawables(const MDagPath& objPath, MHWRender::MUIDrawManager& drawManager, const MHWRender::MFrameContext& frameContext, const MUserData* data)
{
	// Get data cached by prepareForDraw() for each drawable instance, then MUIDrawManager 
	// can draw simple UI by these data.
	tpAnnotationData* pLocatorData = (tpAnnotationData*)data;
	if (!pLocatorData)
	{
		return;
	}

	drawManager.beginDrawable();

	// Draw the foot print solid/wireframe
	drawManager.setColor(pLocatorData->fColor);
	drawManager.setDepthPriority(5);

	// Draw a text "Foot"
	MPoint pos(0.0, 0.0, 0.0); // Position of the text
	MColor textColor(0.1f, 0.8f, 0.8f, 1.0f); // Text color

	drawManager.setColor(textColor);
	drawManager.setFontSize(MHWRender::MUIDrawManager::kSmallFontSize);
	drawManager.text(pos, MString("tpAnnotation"), MHWRender::MUIDrawManager::kCenter);

	drawManager.endDrawable();
}

//---------------------------------------------------------------------------
//---------------------------------------------------------------------------
// Plugin Registration
//---------------------------------------------------------------------------
//---------------------------------------------------------------------------

MStatus tpAnnotation::initialize()
{
	MFnUnitAttribute unitFn;
	MStatus			 stat;

	size = unitFn.create("size", "sz", MFnUnitAttribute::kDistance);
	unitFn.setDefault(1.0);

	stat = addAttribute(size);
	if (!stat) {
		stat.perror("addAttribute");
		return stat;
	}

	return MS::kSuccess;
}

MStatus initializePlugin(MObject obj)
{
	MStatus   status;
	MFnPlugin plugin(obj, PLUGIN_COMPANY, "3.0", "Any");

	status = plugin.registerNode(
		"tpAnnotation",
		tpAnnotation::id,
		&tpAnnotation::creator,
		&tpAnnotation::initialize,
		MPxNode::kLocatorNode,
		&tpAnnotation::drawDbClassification);
	if (!status) {
		status.perror("registerNode");
		return status;
	}

	status = MHWRender::MDrawRegistry::registerDrawOverrideCreator(
		tpAnnotation::drawDbClassification,
		tpAnnotation::drawRegistrantId,
		tpAnnotationDrawOverride::Creator);
	if (!status) {
		status.perror("registerDrawOverrideCreator");
		return status;
	}

	return status;
}

MStatus uninitializePlugin(MObject obj)
{
	MStatus   status;
	MFnPlugin plugin(obj);

	status = MHWRender::MDrawRegistry::deregisterDrawOverrideCreator(
		tpAnnotation::drawDbClassification,
		tpAnnotation::drawRegistrantId);
	if (!status) {
		status.perror("deregisterDrawOverrideCreator");
		return status;
	}

	status = plugin.deregisterNode(tpAnnotation::id);
	if (!status) {
		status.perror("deregisterNode");
		return status;
	}
	return status;
}