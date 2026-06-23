Attribute VB_Name = "Link429Summary"
'======================================================================
' Link429Summary  (v3 - sheet auto-detect by matching known gross)
'
' Makes every figure in the GROSS429 summary a LIVE, CLICKABLE formula
' pulling from the monthly *_WITH_FORMULAE.xlsx files.
'
' WHY v3: monthly files contain SEVERAL sheets. v2 picked the biggest
' sheet, which over-counts (REVISED_GROSS repeats per sub-row -> ~5x).
' v3 instead scans EVERY sheet and uses the one whose REVISED_GROSS column
' SUM matches the month's known-correct gross already in your summary.
' From that confirmed sheet it then links each field BY HEADER NAME,
' verifying every value before it links (mismatch = left as-is + reported).
'
' Also: AUTO-FINDS the summary sheet (no need for a tab named exactly
' "Monthly Summary"); uses a sheet named that, else the sheet with "April"
' in column A, else the ActiveSheet.
'
' SETUP: save a COPY of the summary as .xlsm IN THE SAME FOLDER as ALL 12
'        monthly files (make sure June_WITH_FORMULAE.xlsx is really there),
'        then run. If Excel asks to "Update Links", click Update/Enable.
'======================================================================
Option Explicit

Public Sub Link429Summary()
    Dim months As Variant
    months = Array("April", "May", "June", "July", "August", "September", _
                   "October", "November", "December", "January", "February", "March")
    ' summaryCol | monthly header (normalized: UPPER, spaces/dots/()/-/ removed, UNDERSCORE KEPT)
    Dim map As Variant
    map = Array("3|REVISED_GROSS", "4|REVISED_PF", "5|ESIC1", "6|PT1", "7|LWF1", "8|TDS1", _
        "9|EMPLOYEEWELFAREFUND1", "10|ADVANCE1", "11|UNIFORM1", "12|OTHERDEDUCTION1", _
        "13|FOODDEDUCTION1", "14|FOODDEDUCTIONS1", "15|MOBILEDEDUCTION1", "16|PROFESSIONALFEES1", _
        "17|INSURANCEDEDUCTION1", "18|INSURANCE1", "19|FINE1", "20|ACCOMODATION1", "21|FLEXIDED1", _
        "22|CONVEYANCEALLDED1", "23|LAUNDRYCHARGES1", "24|MEALDEDUCTION1", "25|REFYNEADVANCE1", _
        "27|OTHER_DEDUCTION", "29|REVISED_NET_PAYABLE")

    Dim sumSh As Worksheet: Set sumSh = FindSummarySheet()
    If sumSh Is Nothing Then
        MsgBox "Could not find the summary sheet (the one with 'April' down column A). Open it and run again.", vbExclamation
        Exit Sub
    End If

    Dim folder As String: folder = ThisWorkbook.Path & Application.PathSeparator
    Dim oldCalc As XlCalculation: oldCalc = Application.Calculation
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Application.Calculation = xlCalculationManual
    Dim report As String, linkedCount As Long

    Dim i As Long, rowS As Long, fn As String, wb As Workbook
    For i = 0 To UBound(months)
        rowS = 5 + i
        fn = Dir(folder & months(i) & "*WITH_FORMULAE.xlsx")
        If fn = "" Then report = report & months(i) & ": FILE NOT FOUND in this folder" & vbCrLf: GoTo NextMonth

        Dim grossCur As Double: grossCur = ValD(sumSh.Cells(rowS, 3))
        Set wb = Workbooks.Open(folder & fn, ReadOnly:=True, UpdateLinks:=False)

        ' ---- pick the sheet whose REVISED_GROSS sum matches grossCur ----
        Dim ws As Worksheet, useWs As Worksheet, useHr As Long, useLast As Long
        Dim s As Worksheet, hr As Long, gcol As Long, lastR As Long, gsum As Double
        Dim tol As Double: tol = Application.Max(100, grossCur * 0.0005)   ' ~0.05%
        Dim diag As String
        Set useWs = Nothing
        For Each s In wb.Worksheets
            hr = HeaderRowOf(s, "REVISED_GROSS")
            If hr > 0 Then
                gcol = ColOfHeader(s, hr, "REVISED_GROSS")
                If gcol > 0 Then
                    lastR = s.Cells(s.Rows.Count, gcol).End(xlUp).Row
                    gsum = Application.WorksheetFunction.Sum(s.Range(s.Cells(hr + 1, gcol), s.Cells(lastR, gcol)))
                    diag = diag & "   [" & s.Name & "] gross=" & Format(gsum, "#,##0") & vbCrLf
                    If Abs(gsum - grossCur) <= tol Then
                        Set useWs = s: useHr = hr: useLast = lastR: Exit For
                    End If
                End If
            End If
        Next s

        If useWs Is Nothing Then
            report = report & months(i) & ": no sheet's REVISED_GROSS = " & Format(grossCur, "#,##0") & _
                     " (left as-is). Sheets found:" & vbCrLf & diag
            wb.Close False: GoTo NextMonth
        End If

        ' ---- build header dictionary on the confirmed sheet ----
        Dim dict As Object: Set dict = CreateObject("Scripting.Dictionary")
        Dim c As Long, maxC As Long, t As String
        maxC = useWs.UsedRange.Column + useWs.UsedRange.Columns.Count - 1
        For c = 1 To maxC
            t = NormU(useWs.Cells(useHr, c).Value)
            If Len(t) > 0 Then If Not dict.Exists(t) Then dict.Add t, c
        Next c

        Dim base As String: base = "'" & folder & "[" & fn & "]" & useWs.Name & "'!"

        ' employee rows
        If dict.Exists("EMPCODE") Then
            sumSh.Cells(rowS, 2).Value = Application.WorksheetFunction.CountA( _
                useWs.Range(useWs.Cells(useHr + 1, dict("EMPCODE")), useWs.Cells(useLast, dict("EMPCODE"))))
        End If

        ' ---- link each field (verify value first) ----
        Dim p As Variant, parts() As String, scol As Long, nm As String
        Dim mc As Long, L As String, msum As Double, cur As Double, ftol As Double
        Dim miss As String, mism As String
        For Each p In map
            parts = Split(CStr(p), "|")
            scol = CLng(parts(0)): nm = parts(1)
            If Not dict.Exists(nm) Then miss = miss & nm & " ": GoTo NextField
            mc = dict(nm): L = ColLetter(mc)
            msum = Application.WorksheetFunction.Sum(useWs.Range(useWs.Cells(useHr + 1, mc), useWs.Cells(useLast, mc)))
            cur = ValD(sumSh.Cells(rowS, scol))
            ftol = Application.Max(50, Abs(cur) * 0.001)
            If Abs(msum - cur) <= ftol Then
                sumSh.Cells(rowS, scol).Formula = "=SUM(" & base & "$" & L & "$" & (useHr + 1) & ":$" & L & "$" & useLast & ")"
                sumSh.Cells(rowS, scol).NumberFormat = "#,##0"
                linkedCount = linkedCount + 1
            Else
                mism = mism & nm & "(file " & Format(msum, "#,##0") & " vs sheet " & Format(cur, "#,##0") & ") "
            End If
NextField:
        Next p
        report = report & months(i) & ": sheet '" & useWs.Name & "' OK." & vbCrLf
        If Len(miss) > 0 Then report = report & "    not found -> " & miss & vbCrLf
        If Len(mism) > 0 Then report = report & "    value differs (left as-is) -> " & mism & vbCrLf

        wb.Close SaveChanges:=False
NextMonth:
    Next i

    Application.Calculation = oldCalc
    Application.Calculate
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    MsgBox "GROSS429 linking finished. Cells linked: " & linkedCount & vbCrLf & _
           "Summary sheet: '" & sumSh.Name & "'" & vbCrLf & vbCrLf & report, vbInformation
End Sub

' ---- helpers --------------------------------------------------------
' first row (1..20) on sheet sh that contains the given normalized header
Private Function HeaderRowOf(sh As Worksheet, ByVal want As String) As Long
    Dim r As Long, c As Long, maxC As Long
    On Error Resume Next
    maxC = sh.UsedRange.Column + sh.UsedRange.Columns.Count - 1
    On Error GoTo 0
    If maxC < 1 Or maxC > 2000 Then maxC = 260
    For r = 1 To 20
        For c = 1 To maxC
            If NormU(sh.Cells(r, c).Value) = want Then HeaderRowOf = r: Exit Function
        Next c
    Next r
    HeaderRowOf = 0
End Function

Private Function ColOfHeader(sh As Worksheet, ByVal hr As Long, ByVal want As String) As Long
    Dim c As Long, maxC As Long
    maxC = sh.UsedRange.Column + sh.UsedRange.Columns.Count - 1
    If maxC < 1 Or maxC > 2000 Then maxC = 260
    For c = 1 To maxC
        If NormU(sh.Cells(hr, c).Value) = want Then ColOfHeader = c: Exit Function
    Next c
    ColOfHeader = 0
End Function

Private Function FindSummarySheet() As Worksheet
    Dim sh As Worksheet, r As Long
    On Error Resume Next
    Set FindSummarySheet = ThisWorkbook.Sheets("Monthly Summary")
    On Error GoTo 0
    If Not FindSummarySheet Is Nothing Then Exit Function
    For Each sh In ThisWorkbook.Worksheets
        For r = 1 To 20
            If Trim(UCase(CStr(sh.Cells(r, 1).Value))) = "APRIL" Then
                Set FindSummarySheet = sh: Exit Function
            End If
        Next r
    Next sh
    If TypeName(ThisWorkbook.ActiveSheet) = "Worksheet" Then Set FindSummarySheet = ThisWorkbook.ActiveSheet
End Function

Private Function NormU(v As Variant) As String
    Dim s As String: s = UCase(CStr(v))
    Dim ch As Variant
    For Each ch In Array(" ", ".", "(", ")", "-", "/", vbLf, vbCr)   ' underscore KEPT
        s = Replace(s, CStr(ch), "")
    Next ch
    NormU = s
End Function

Private Function ValD(v As Variant) As Double
    If IsError(v) Then ValD = 0: Exit Function
    If IsNumeric(v) Then ValD = CDbl(v) Else ValD = 0
End Function

Private Function ColLetter(ByVal n As Long) As String
    Dim s As String, r As Long
    Do While n > 0
        r = (n - 1) Mod 26: s = Chr(65 + r) & s: n = (n - 1) \ 26
    Loop
    ColLetter = s
End Function
