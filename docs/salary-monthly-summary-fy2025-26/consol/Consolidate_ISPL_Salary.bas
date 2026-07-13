Attribute VB_Name = "Consolidate_ISPL_Salary"
'=====================================================================
' ISPL SALARY AUDIT - 12-month consolidation macro (revised block)
'---------------------------------------------------------------------
' What it does (same logic Claude ran server-side for FY 2025-26):
'  1. Loops over every *M13_FINAL*.xlsx in FOLDER_PATH
'  2. On sheet "Salary (Corrected)", finds the header row (the row
'     containing EMPCODE) - header position varies by month
'  3. Picks columns BY NAME (positions like GC:HK change every month):
'     ID cols + ADJ_WORKING_DAYS .. REVISED_NET_PAYABLE + NETPAYABLE
'  4. Appends all rows to a CONSOL sheet with a MONTH column
'  5. Builds a PivotTable: rows = MONTH, values = sum of every measure
'---------------------------------------------------------------------
' HOW TO USE: copy the 12 monthly files into one local folder, set
' FOLDER_PATH below, open a blank workbook, Alt+F11 > import this
' module, then run ConsolidateISPL.  Runtime ~2-4 min for 12 files.
'=====================================================================
Option Explicit

Const FOLDER_PATH As String = "C:\ISPL\ESI_WASHING_REALLOCATED\"   ' <-- change me
Const SHEET_NAME As String = "Salary (Corrected)"

' canonical output columns; pipe-separated alternatives are tried in order
Const WANTED As String = _
    "SITECODE|SITENAME|SITESTATE|EMPCODE|FULLNAME|NETPAYABLE|" & _
    "ADJ_WORKING_DAYS|REVISED_BASIC|REVISED_DA|REVISED_ATTENDANCE_ALLOWANCE|" & _
    "REVISED_GROSS|REVISED_GROSS_NEW (final)~REVISED_GROSS_NEW|ECR_PF|REVISED_PF|" & _
    "ESIC.1~REVISED_ESIC|ESIC AS PER FUTURE~ESIC_AS_PER_FUTURE~Future_ESI|" & _
    "PT.1~PT|LWF.1~LWF|UNIFORM.1~UNIFORM|ADVANCE.1~ADVANCE|TDS.1~TDS|" & _
    "EMPLOYEE WELFARE FUND.1~EMPLOYEE WELFARE FUND|FOOD DEDUCTION.1~FOOD DEDUCTION|" & _
    "OTHER_DEDUCTION~REVISED_OTHER_DEDUCTION|REVISED_TOTAL_DED|REVISED_NET_PAYABLE"

Sub ConsolidateISPL()
    Dim fso As Object, f As Object, wbSrc As Workbook, wsSrc As Worksheet
    Dim wsOut As Worksheet, wanted() As String, nW As Long, outRow As Long
    Dim hdrRow As Long, lastRow As Long, lastCol As Long, i As Long, j As Long, k As Long
    Dim colIdx() As Long, alts() As String, monthLbl As String

    Application.ScreenUpdating = False: Application.Calculation = xlCalculationManual
    wanted = Split(WANTED, "|"): nW = UBound(wanted) + 1

    Set wsOut = ThisWorkbook.Worksheets.Add: wsOut.Name = "CONSOL"
    wsOut.Cells(1, 1).Value = "MONTH"
    For j = 0 To nW - 1
        wsOut.Cells(1, j + 2).Value = Split(wanted(j), "~")(0) ' canonical name
    Next j
    outRow = 2

    Set fso = CreateObject("Scripting.FileSystemObject")
    For Each f In fso.GetFolder(FOLDER_PATH).Files
        If f.Name Like "*M13_FINAL*.xls*" And Not f.Name Like "~$*" Then
            Set wbSrc = Workbooks.Open(f.Path, ReadOnly:=True, UpdateLinks:=0)
            Set wsSrc = wbSrc.Worksheets(SHEET_NAME)
            monthLbl = Split(f.Name, "_")(0)              ' e.g. "April" from April_M13_FINAL

            ' locate header row = first row containing EMPCODE in first 10 rows
            hdrRow = 0
            For i = 1 To 10
                If Not wsSrc.Rows(i).Find("EMPCODE", LookAt:=xlWhole) Is Nothing Then hdrRow = i: Exit For
            Next i
            If hdrRow = 0 Then MsgBox "EMPCODE header not found in " & f.Name: GoTo NextFile

            lastCol = wsSrc.Cells(hdrRow, wsSrc.Columns.Count).End(xlToLeft).Column
            lastRow = wsSrc.Cells(wsSrc.Rows.Count, "N").End(xlUp).Row ' EMPCODE-ish col; adjust if needed
            If lastRow <= hdrRow Then lastRow = wsSrc.UsedRange.Rows.Count

            ' map wanted -> source col index (first matching alternative, FIRST occurrence)
            ReDim colIdx(0 To nW - 1)
            For j = 0 To nW - 1
                colIdx(j) = 0: alts = Split(wanted(j), "~")
                For k = 0 To UBound(alts)
                    Dim c As Range
                    Set c = wsSrc.Rows(hdrRow).Find(alts(k), LookAt:=xlWhole, MatchCase:=False)
                    If Not c Is Nothing Then colIdx(j) = c.Column: Exit For
                Next k
            Next j

            ' copy values month by month
            Dim buf() As Variant, r As Long
            For r = hdrRow + 1 To lastRow
                If Len(Trim$(CStr(wsSrc.Cells(r, colIdx(3)).Value))) > 0 Then ' EMPCODE not blank
                    wsOut.Cells(outRow, 1).Value = monthLbl
                    For j = 0 To nW - 1
                        If colIdx(j) > 0 Then wsOut.Cells(outRow, j + 2).Value = wsSrc.Cells(r, colIdx(j)).Value
                    Next j
                    outRow = outRow + 1
                End If
            Next r
NextFile:
            wbSrc.Close SaveChanges:=False
        End If
    Next f

    ' ---- pivot table: rows=MONTH, sum of every numeric measure ----
    Dim pc As PivotCache, pt As PivotTable, wsPv As Worksheet, pf As PivotField
    Set wsPv = ThisWorkbook.Worksheets.Add: wsPv.Name = "PIVOT_12M"
    Set pc = ThisWorkbook.PivotCaches.Create(xlDatabase, wsOut.Range("A1").CurrentRegion)
    Set pt = pc.CreatePivotTable(wsPv.Range("A3"), "Pivot12M")
    pt.PivotFields("MONTH").Orientation = xlRowField
    Dim measures As Variant
    measures = Array("REVISED_BASIC", "REVISED_DA", "REVISED_ATTENDANCE_ALLOWANCE", _
        "REVISED_GROSS", "REVISED_PF", "ESIC.1", "OTHER_DEDUCTION", "REVISED_TOTAL_DED", _
        "REVISED_NET_PAYABLE", "NETPAYABLE")
    For j = 0 To UBound(measures)
        On Error Resume Next
        pt.AddDataField pt.PivotFields(CStr(measures(j))), "Sum " & measures(j), xlSum
        On Error GoTo 0
    Next j

    Application.Calculation = xlCalculationAutomatic: Application.ScreenUpdating = True
    MsgBox "Done. CONSOL rows: " & outRow - 2 & ". Check that Sum REVISED_NET_PAYABLE = Sum NETPAYABLE (golden rule).", vbInformation
End Sub
