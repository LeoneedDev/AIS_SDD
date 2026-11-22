/*
 * Export diagramov do PNG pre spec/architecture/views/
 * Sparx EA → Specialize → Scripting → New JavaScript Script → vlož → Run.
 * Skript nič v modeli nemení, iba ukladá obrázky.
 */

// Cieľový priečinok (musí existovať):
var OUTPUT_DIR = "C:\\Users\\aboba\\AIS_SDD\\spec\\architecture\\views\\";

var VIEWS = [
    { id: 52, name: "Layered Viewpoint",                      file: "layered.png" },
    { id: 64, name: "Service Realization Viewpoint",          file: "service-realization.png" },
    { id: 51, name: "Aplication Usage Viewpoint",             file: "application-usage.png" },
    { id: 50, name: "Application Cooperation Viewpoint",      file: "application-cooperation.png" },
    { id: 54, name: "Application Structure Viewpoint",        file: "application-structure.png" },
    { id: 47, name: "Business Process Cooperation Viewpoint", file: "business-process-cooperation.png" },
    { id: 60, name: "Information Structure Viewpoint",        file: "information-structure.png" },
    { id: 48, name: "Requirements Realization Viewpoint",     file: "requirements-realization.png" }
];

function main() {
    Repository.EnsureOutputVisible("Script");
    Repository.ClearOutput("Script");
    var project = Repository.GetProjectInterface();
    var ok = 0;
    for (var i = 0; i < VIEWS.length; i++) {
        var v = VIEWS[i];
        var d = null;
        try { d = Repository.GetDiagramByID(v.id); } catch (ex) { d = null; }
        if (d == null || d.Name != v.name) {
            Session.Output("CHYBA: diagram #" + v.id + " nie je '" + v.name + "'" + (d ? " (je '" + d.Name + "')" : ""));
            continue;
        }
        var path = OUTPUT_DIR + v.file;
        // typ 1 = formát podľa prípony súboru (.png)
        var res = project.PutDiagramImageToFile(project.GUIDtoXML(d.DiagramGUID), path, 1);
        Session.Output((res ? "  + " : "  ! nepodarilo sa: ") + v.name + " → " + path);
        if (res) ok++;
    }
    Session.Output("=== Hotovo: " + ok + " / " + VIEWS.length + " ===");
}

main();
