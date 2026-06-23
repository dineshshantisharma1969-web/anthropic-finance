Attribute VB_Name = "Link429Summary"
'======================================================================
' Link429Summary  (v6 - month from FILENAME, columns by value fingerprint)
'
' Runs on the folder this summary sits in. For each monthly file it:
'   1) reads the MONTH from the file name (April..March),
'      falling back to gross-matching only if the name has no month,
'   2) opens it, sums every column,
'   3) links each figure in that month's summary row to the column whose
'      total matches it (so header names don't matter).
' Nothing wrong is ever written - unmatched figures are just reported.
'
' IMPORTANT: start from a FRESH copy of the summary (un-linked values),
' save it as .xlsm IN THE 429-cr FOLDER, then run.
'======================================================================
Option Explicit

Public Sub Link429Summary()
    Dim sumSh As Worksheet: Set sumSh = FindSummarySheet()
    If sumSh Is Nothing Then
        MsgBox "Open the summary (sheet with 'April' down column A) and run again.", vbExclamation
        Exit Sub
    End If

    Dim map As Variant
    map = Array("3|Revised Gross", "4|PF", "5|ESI", "6|PT", "7|LWF", "8|TDS", _
        "9|Emp Welfare Fund", "10|Advance", "11|Uniform", "12|Other Ded (entered)", _
        "13|Food Ded", "14|Food Deds", "15|Mobile Ded", "16|Professional Fees", _
        "17|Insurance Ded", "18|Insurance", "19|Fine", "20|Accomodation", "21|Flexi Ded", _
        "22|Conveyance Ded", "23|Laundry", "24|Meal Ded", "25|Refyne Adv", _
        "27|Other Ded (residual)", "29|Net Payable")
    Dim monthName As Variant
    monthName = Array("April", "May", "June", "July", "August", "September", _
                      "October", "November", "December", "January", "February", "March")

    Dim G(0 To 11) As Double, taken(0 To 11) As Boolean, i As Long
    For i = 0 To 11: G(i) = ValD(sumSh.Cells(5 + i, 3)): Next i

    Dim folder As String: folder = ThisWorkbook.Path & Application.PathSeparator
    Dim oldCalc As XlCalculation: oldCalc = Application.Calculation
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Application.Calculation = xlCalculationManual

    Dim report As String, grandLinked As Long
    Dim fn As String, files() As String, nF As Long: ReDim files(1 To 500): nF = 0
    fn = Dir(folder & "*.xls*")
    Do While fn <> ""
        If Left$(fn, 2) <> "~$" And LCase(fn) <> LCase(ThisWorkbook.Name) Then nF = nF + 1: files(nF) = fn
        fn = Dir
    Loop

    Dim k As Long, wb As Workbook
    For k = 1 To nF
        ' ---- month from file name first ----
        Dim m As Long, bestM As Long
        bestM = -1
        Dim up As String: up = UCase(files(k))
        For m = 0 To 11
            If InStr(up, UCase(CStr(monthName(m)))) > 0 And Not taken(m) Then bestM = m: Exit For
        Next m

        Set wb = Workbooks.Open(folder & files(k), ReadOnly:=True, UpdateLinks:=False)
        Dim ws As Worksheet, s As Worksheet, best As Long
        best = 0: Set ws = Nothing
        For Each s In wb.Worksheets
            If s.UsedRange.Rows.Count > best Then best = s.UsedRange.Rows.Count: Set ws = s
        Next s

        Dim hr As Long, lastR As Long, maxC As Long, c As Long
        maxC = ws.UsedRange.Column + ws.UsedRange.Columns.Count - 1
        If maxC < 1 Or maxC > 1000 Then maxC = 260
        lastR = ws.UsedRange.Row + ws.UsedRange.Rows.Count - 1
        hr = HeaderRowOf(ws, maxC)

        Dim csum() As Double: ReDim csum(1 To maxC)
        For c = 1 To maxC
            csum(c) = Application.WorksheetFunction.Sum(ws.Range(ws.Cells(hr + 1, c), ws.Cells(lastR, c)))
        Next c

        ' ---- if name gave no month, fall back to gross match ----
        If bestM < 0 Then
            Dim rel As Double, bestErr As Double: bestErr = 1E+99
            For m = 0 To 11
                If Not taken(m) And G(m) > 1 Then
                    For c = 1 To maxC
                        rel = Abs(csum(c) - G(m)) / G(m)
                        If rel <= 0.005 And rel < bestErr Then bestErr = rel: bestM = m
                    Next c
                End If
            Next m
        End If

        If bestM < 0 Then
            report = report & files(k) & ": could not identify month - skipped" & vbCrLf
            wb.Close False: GoTo NextFile
        End If
        taken(bestM) = True
        Dim rowS As Long: rowS = 5 + bestM
        Dim base As String: base = "'" & folder & "[" & files(k) & "]" & ws.Name & "'!"

        Dim ecCol As Long: ecCol = ColByName(ws, hr, maxC, "EMPCODE")
        If ecCol > 0 Then sumSh.Cells(rowS, 2).Value = _
            Application.WorksheetFunction.CountA(ws.Range(ws.Cells(hr + 1, ecCol), ws.Cells(lastR, ecCol)))

        ' ---- link fields by value (reset counters PER FILE) ----
        Dim p As Variant, parts() As String, scol As Long, lbl As String
        Dim cur As Double, tol As Double, found As Long
        Dim monthLinked As Long, misses As String
        monthLinked = 0: misses = ""
        For Each p In map
            parts = Split(CStr(p), "|")
            scol = CLng(parts(0)): lbl = parts(1)
            cur = ValD(sumSh.Cells(rowS, scol))
            If Abs(cur) < 1 Then GoTo NextField
            tol = Application.Max(50, Abs(cur) * 0.001)
            found = 0
            For c = 1 To maxC
                If Abs(csum(c) - cur) <= tol Then found = c: Exit For
            Next c
            If found > 0 Then
                sumSh.Cells(rowS, scol).Formula = "=SUM(" & base & "$" & ColLetter(found) & "$" & (hr + 1) & ":$" & ColLetter(found) & "$" & lastR & ")"
                sumSh.Cells(rowS, scol).NumberFormat = "#,##0"
                monthLinked = monthLinked + 1: grandLinked = grandLinked + 1
            Else
                misses = misses & lbl & " "
            End If
NextField:
        Next p

        report = report & monthName(bestM) & " = " & files(k) & "  -> " & monthLinked & "/25" & vbCrLf
        If Len(misses) > 0 Then report = report & "      not matched: " & misses & vbCrLf
        wb.Close SaveChanges:=False
NextFile:
    Next k

    Dim leftover As String
    For m = 0 To 11
        If Not taken(m) Then leftover = leftover & monthName(m) & " "
    Next m
    If Len(leftover) > 0 Then report = report & "NO FILE for: " & leftover & vbCrLf

    Application.Calculation = oldCalc
    Application.Calculate
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    MsgBox "Done. Total cells linked: " & grandLinked & vbCrLf & vbCrLf & report, vbInformation
End Sub

' ---- helpers --------------------------------------------------------
Private Function HeaderRowOf(ws As Worksheet, ByVal maxC As Long) As Long
    Dim r As Long, c As Long, t As String
    For r = 1 To 20
        For c = 1 To maxC
            t = NormU(ws.Cells(r, c).Value)
            If t = "EMPCODE" Or t = "REVISED_GROSS" Or t = "REVISEDGROSS" Or t = "GROSSAMT" Then HeaderRowOf = r: Exit Function
        Next c
    Next r
    HeaderRowOf = 1
End Function

Private Function ColByName(ws As Worksheet, ByVal hr As Long, ByVal maxC As Long, ByVal want As String) As Long
    Dim c As Long
    For c = 1 To maxC
        If NormU(ws.Cells(hr, c).Value) = want Then ColByName = c: Exit Function
    Next c
    ColByName = 0
End Function

Private Function FindSummarySheet() As Worksheet
    Dim sh As Worksheet, r As Long
    On Error Resume Next
    Set FindSummarySheet = ThisWorkbook.Sheets("Monthly Summary")
    On Error GoTo 0
    If Not FindSummarySheet Is Nothing Then Exit Function
    For Each sh In ThisWorkbook.Worksheets
        For r = 1 To 20
            If Trim(UCase(CStr(sh.Cells(r, 1).Value))) = "APRIL" Then Set FindSummarySheet = sh: Exit Function
        Next r
    Next sh
    If TypeName(ThisWorkbook.ActiveSheet) = "Worksheet" Then Set FindSummarySheet = ThisWorkbook.ActiveSheet
End Function

Private Function NormU(v As Variant) As String
    Dim s As String: s = UCase(CStr(v))
    Dim ch As Variant
    For Each ch In Array(" ", ".", "(", ")", "-", "/", vbLf, vbCr)
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
