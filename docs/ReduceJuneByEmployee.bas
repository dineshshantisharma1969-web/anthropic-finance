Attribute VB_Name = "ReduceJuneByEmployee"
'======================================================================
' ReduceJuneByEmployee  -  June FY25-26 reduce REVISED GROSS to 380cr,
' keeping each EMPLOYEE's Net Payable unchanged (across their rows).
'
' Columns in THIS file (confirmed):
'   EMP CODE ............ L  (12)
'   REVISED ATTEND. ALLOW GC (185)   <- reduce this to lower gross
'   REVISED GROSS ....... GF (188)
'   OTHER DEDUCTION ..... GI (191)   <- absorbs (decreases) to hold net
'   REVISED TOTAL DED ... GJ (192)
'   REVISED NET PAYABLE . GK (193)   <- kept unchanged per employee
'
' Method per employee: reduce attendance allowance on att rows (gross down)
' and reduce Other Deduction on od rows by the SAME total (total-ded down),
' so the employee's Net Payable is preserved. ESI-exempt rows (gross>21000)
' are never taken below 21000. Covered employees processed first.
'
' RUN:  open file -> Alt+F11 -> Insert Module -> (Import this .bas, or paste
'       the code WITHOUT the first 'Attribute' line) -> F5 -> read message.
'======================================================================
Option Explicit

Public Sub ReduceJuneByEmployee()
    Const TARGET As Double = 298950541#      ' Rs 29,89,50,541
    Const FLOORv As Double = 21000#
    Const cEMP As Long = 12                   ' L
    Const cATT As Long = 185                  ' GC
    Const cGROSS As Long = 188                ' GF
    Const cOD As Long = 191                   ' GI
    Const cTD As Long = 192                   ' GJ
    Const cNET As Long = 193                  ' GK

    Dim ws As Worksheet, s As Worksheet, best As Long
    For Each s In ThisWorkbook.Worksheets
        If s.UsedRange.Rows.Count > best Then best = s.UsedRange.Rows.Count: Set ws = s
    Next s

    Dim lastRow As Long, rw As Long
    lastRow = ws.Cells(ws.Rows.Count, cGROSS).End(xlUp).Row

    ' group employee rows (skip header/blank/total rows: need empcode + numeric gross>0)
    Dim dict As Object: Set dict = CreateObject("Scripting.Dictionary")
    Dim curGross As Double, curNet As Double, key As String, g As Double
    For rw = 1 To lastRow
        If Len(Trim(CStr(ws.Cells(rw, cEMP).Value))) > 0 Then
            If IsNumeric(ws.Cells(rw, cGROSS).Value) Then
                g = CDbl(ws.Cells(rw, cGROSS).Value)
                If g > 0 Then
                    key = Trim(CStr(ws.Cells(rw, cEMP).Value))
                    If Not dict.Exists(key) Then dict.Add key, New Collection
                    dict(key).Add rw
                    curGross = curGross + g
                    curNet = curNet + V0(ws.Cells(rw, cNET).Value)
                End If
            End If
        End If
    Next rw

    Dim needed As Double: needed = curGross - TARGET
    If needed <= 0 Then
        MsgBox "Nothing to reduce. Current gross = " & Format(curGross, "#,##0"), vbInformation
        Exit Sub
    End If

    Dim netFormula As Boolean, grFormula As Boolean, tdFormula As Boolean
    netFormula = ws.Cells(dict(dict.Keys()(0))(1), cNET).HasFormula
    grFormula = ws.Cells(dict(dict.Keys()(0))(1), cGROSS).HasFormula
    tdFormula = ws.Cells(dict(dict.Keys()(0))(1), cTD).HasFormula

    ' total capacity (for reporting)
    Dim k As Variant, rr As Variant, totCap As Double
    For Each k In dict.Keys
        totCap = totCap + EmpCap(ws, dict(k), cATT, cGROSS, cOD, FLOORv)
    Next k

    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual

    Dim remaining As Double: remaining = needed
    Dim pass As Integer
    For pass = 1 To 2                          ' 1 = covered employees first
        For Each k In dict.Keys
            If remaining <= 0 Then Exit For
            Dim covered As Boolean: covered = IsCovered(ws, dict(k), cGROSS, FLOORv)
            If (pass = 1 And covered) Or (pass = 2 And Not covered) Then
                Dim capE As Double: capE = EmpCap(ws, dict(k), cATT, cGROSS, cOD, FLOORv)
                Dim dE As Double: dE = remaining
                If capE < dE Then dE = capE
                If dE > 0 Then
                    ' take dE from attendance allowance (lower gross)
                    Dim need As Double, t As Double, a As Double, aRed As Double, gg As Double
                    need = dE
                    For Each rr In dict(k)
                        If need <= 0 Then Exit For
                        gg = V0(ws.Cells(rr, cGROSS).Value)
                        a = V0(ws.Cells(rr, cATT).Value)
                        aRed = a
                        If gg > FLOORv Then If (gg - FLOORv) < aRed Then aRed = gg - FLOORv
                        If aRed < 0 Then aRed = 0
                        t = need: If aRed < t Then t = aRed
                        If t > 0 Then
                            ws.Cells(rr, cATT).Value = Round(a - t, 2)
                            If Not grFormula Then ws.Cells(rr, cGROSS).Value = Round(gg - t, 2)
                            need = need - t
                        End If
                    Next rr
                    ' take dE from Other Deduction (lower total deduction)
                    Dim od As Double
                    need = dE
                    For Each rr In dict(k)
                        If need <= 0 Then Exit For
                        od = V0(ws.Cells(rr, cOD).Value)
                        t = need: If od < t Then t = od
                        If t > 0 Then
                            ws.Cells(rr, cOD).Value = Round(od - t, 2)
                            If Not tdFormula Then ws.Cells(rr, cTD).Value = Round(V0(ws.Cells(rr, cTD).Value) - t, 2)
                            need = need - t
                        End If
                    Next rr
                    ' keep net = gross - totded consistent if net is a stored value
                    If Not netFormula Then
                        For Each rr In dict(k)
                            ws.Cells(rr, cNET).Value = Round(V0(ws.Cells(rr, cGROSS).Value) - V0(ws.Cells(rr, cTD).Value), 2)
                        Next rr
                    End If
                    remaining = remaining - dE
                End If
            End If
        Next k
    Next pass

    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True

    ' recompute new net total for the report
    Dim newNet As Double, newGross As Double
    For Each k In dict.Keys
        For Each rr In dict(k)
            newGross = newGross + V0(ws.Cells(rr, cGROSS).Value)
            newNet = newNet + V0(ws.Cells(rr, cNET).Value)
        Next rr
    Next k

    Dim m As String
    m = "JUNE employee-grouped reduction" & vbCrLf & vbCrLf
    m = m & "Employees      : " & dict.Count & vbCrLf
    m = m & "Old gross      : " & Format(curGross, "#,##0") & vbCrLf
    m = m & "Target gross   : " & Format(TARGET, "#,##0") & vbCrLf
    m = m & "Needed cut     : " & Format(needed, "#,##0") & vbCrLf
    m = m & "Total capacity : " & Format(totCap, "#,##0") & vbCrLf
    m = m & "Allocated      : " & Format(needed - remaining, "#,##0") & vbCrLf
    m = m & "New gross      : " & Format(newGross, "#,##0") & vbCrLf
    m = m & "Net (old->new) : " & Format(curNet, "#,##0") & " -> " & Format(newNet, "#,##0")
    If remaining > 1 Then
        m = m & vbCrLf & vbCrLf & "WARNING: Rs " & Format(remaining, "#,##0") & " could NOT be cut " & _
            "(not enough employees have both attendance-allowance and other-deduction rows). " & _
            "Do not save; use the summary-level fix instead, or re-run the original June build script."
        MsgBox m, vbExclamation
    Else
        m = m & vbCrLf & vbCrLf & "Full amount allocated. Net per employee unchanged. Save (keep .xlsx)."
        MsgBox m, vbInformation
    End If
End Sub

Private Function V0(v As Variant) As Double
    If IsError(v) Then V0 = 0: Exit Function
    If IsNumeric(v) Then V0 = CDbl(v) Else V0 = 0
End Function

Private Function EmpCap(ws As Worksheet, rows As Collection, cATT As Long, cGROSS As Long, cOD As Long, FLOORv As Double) As Double
    Dim rr As Variant, attc As Double, odc As Double, a As Double, g As Double, aRed As Double
    For Each rr In rows
        g = V0(ws.Cells(rr, cGROSS).Value): a = V0(ws.Cells(rr, cATT).Value)
        aRed = a
        If g > FLOORv Then If (g - FLOORv) < aRed Then aRed = g - FLOORv
        If aRed < 0 Then aRed = 0
        attc = attc + aRed
        odc = odc + V0(ws.Cells(rr, cOD).Value)
    Next rr
    EmpCap = IIf(attc < odc, attc, odc)
End Function

Private Function IsCovered(ws As Worksheet, rows As Collection, cGROSS As Long, FLOORv As Double) As Boolean
    Dim rr As Variant
    IsCovered = True
    For Each rr In rows
        If V0(ws.Cells(rr, cGROSS).Value) > FLOORv Then IsCovered = False: Exit Function
    Next rr
End Function
