Attribute VB_Name = "FixJune380"
'======================================================================
' FixJune380  -  brings JUNE Revised Gross to exactly Rs 29,89,50,541
' and lowers Other Deduction by the same amount so NET PAYABLE is unchanged.
' SAFE TO RUN MULTIPLE TIMES: it targets the final figure, so a second run
' finds nothing to do (no double-reduction).
'
' Columns in this file:  ATT ALLOW = GC(185)  GROSS = GF(188)
'                        OTHER DED = GI(191)  TOTAL DED = GJ(192)
'
' RUN on a FRESH copy of June_WITH_FORMULAE.xlsx:
'   Alt+F11 -> File > Import File > FixJune380.bas -> F5 -> read box -> Save
'======================================================================
Option Explicit

Public Sub FixJune380()
    Const TARGET As Double = 298950541#    ' Rs 29,89,50,541  (the 380-cr figure)
    Const cATT   As Long = 185             ' GC  attendance allowance
    Const cGROSS As Long = 188             ' GF  revised gross
    Const cOD    As Long = 191             ' GI  other deduction
    Const cTD    As Long = 192             ' GJ  revised total ded
    Const FLOORv As Double = 21000#

    Dim ws As Worksheet: Set ws = ActiveSheet
    Dim lastRow As Long, r As Long
    Dim curGross As Double, v As Double, g As Double, t As Double, cap As Double

    lastRow = ws.Cells(ws.Rows.Count, cGROSS).End(xlUp).Row
    For r = 1 To lastRow
        If IsNumeric(ws.Cells(r, cGROSS).Value) Then
            v = ws.Cells(r, cGROSS).Value
            If v > 0 Then curGross = curGross + v
        End If
    Next r

    Dim needed As Double: needed = curGross - TARGET
    If needed <= 1 Then
        MsgBox "June gross is already " & Format(curGross, "#,##0") & _
               " (target " & Format(TARGET, "#,##0") & "). No change needed.", vbInformation
        Exit Sub
    End If

    Application.Calculation = xlCalculationManual
    Application.ScreenUpdating = False

    ' 1) lower GROSS to target by trimming ATTENDANCE ALLOWANCE
    Dim balA As Double: balA = needed
    For r = 1 To lastRow
        If balA <= 0 Then Exit For
        If IsNumeric(ws.Cells(r, cATT).Value) And IsNumeric(ws.Cells(r, cGROSS).Value) Then
            v = ws.Cells(r, cATT).Value: g = ws.Cells(r, cGROSS).Value
            If v > 0 And g > 0 Then
                cap = v
                If g > FLOORv Then If (g - FLOORv) < cap Then cap = g - FLOORv
                If cap < 0 Then cap = 0
                t = balA: If cap < t Then t = cap
                If t > 0 Then
                    ws.Cells(r, cATT).Value = v - t
                    If Not ws.Cells(r, cGROSS).HasFormula Then ws.Cells(r, cGROSS).Value = g - t
                    balA = balA - t
                End If
            End If
        End If
    Next r

    ' 2) lower OTHER DEDUCTION by the same total (keeps NET unchanged)
    Dim balO As Double: balO = needed
    For r = 1 To lastRow
        If balO <= 0 Then Exit For
        If IsNumeric(ws.Cells(r, cOD).Value) Then
            v = ws.Cells(r, cOD).Value
            If v > 0 Then
                t = balO: If v < t Then t = v
                ws.Cells(r, cOD).Value = v - t
                If Not ws.Cells(r, cTD).HasFormula Then _
                    ws.Cells(r, cTD).Value = ws.Cells(r, cTD).Value - t
                balO = balO - t
            End If
        End If
    Next r

    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True

    ' recompute new gross for the report
    Dim newGross As Double
    For r = 1 To lastRow
        If IsNumeric(ws.Cells(r, cGROSS).Value) Then
            v = ws.Cells(r, cGROSS).Value
            If v > 0 Then newGross = newGross + v
        End If
    Next r

    Dim m As String
    m = "JUNE fix" & vbCrLf & vbCrLf
    m = m & "Old gross         : " & Format(curGross, "#,##0") & vbCrLf
    m = m & "Target gross      : " & Format(TARGET, "#,##0") & vbCrLf
    m = m & "New gross         : " & Format(newGross, "#,##0") & vbCrLf
    m = m & "Gross trimmed     : " & Format(needed - balA, "#,##0") & vbCrLf
    m = m & "Other Ded trimmed : " & Format(needed - balO, "#,##0")
    If balA > 1 Or balO > 1 Then
        m = m & vbCrLf & vbCrLf & "WARNING: could not trim fully (att short " & _
            Format(balA, "#,##0") & ", OD short " & Format(balO, "#,##0") & "). Do not save; tell support."
        MsgBox m, vbExclamation
    Else
        m = m & vbCrLf & vbCrLf & "Done. Gross = target, Net unchanged. Save the file (.xlsx)."
        MsgBox m, vbInformation
    End If
End Sub
