/*
===========================================================================
Copyright (C) 2015 the OpenMoHAA team

This file is part of OpenMoHAA source code.

OpenMoHAA source code is free software; you can redistribute it
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

OpenMoHAA source code is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenMoHAA source code; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
===========================================================================
*/

#pragma once

class linkstring
{
public:
    str value;
    str string;

    linkstring(str value, str string);
};

inline linkstring::linkstring(str value, str string)
{
    this->value  = value;
    this->string = string;
}

class UILabel : public UIWidget
{
    str                     label;
    Container<linkstring *> m_linkstrings;
    qboolean                m_bLinkCvarToShader;
    str                     m_sCurrentShaderName;
    str                     m_sOneShotSoundName;
    str                     m_sLoopingSoundName;
    qboolean                m_bOneShotTriggered;
    float                   m_fOneShotSoundTime;
    int                     m_iNextOneShotTime;
    float                   m_fLoopingSoundStartVolume;
    float                   m_fLoopingSoundHoldStartTime;
    float                   m_fLoopingSoundEndVolume;
    float                   m_fLoopingSoundRampTime;
    int                     m_iNextStateTime;
    int                     m_iSoundState;
    int                     m_iLastEnterTime;
    int                     m_iLastDrawTime;

protected:
    qboolean m_bOutlinedText;
    float    m_wrapLineHeight; // Added in OpenMOHAA Plus: see WordWrap
    Container<str> m_textPieces; // Added in OpenMOHAA Plus: see AddText

    // Added in OpenMOHAA Plus: the text broken into lines that fit the label at m_wrapLineHeight
    void WrapText(const str& text, Container<str>& lines, vec2_t scale);

public:
    CLASS_PROTOTYPE(UILabel);

private:
    void MouseEntered(Event *ev);
    void MouseExited(Event *ev);
    void LinkString(Event *ev);
    int  FindLinkString(str val);
    void LabelLayoutShader(Event *ev);
    void LabelLayoutTileShader(Event *ev);
    // Added in 2.0
    //====
    void OneShotSound(Event *ev);
    void LoopingSound(Event *ev);
    void EventSetOutlinedText(Event *ev);
    void WordWrap(Event *ev);                  // Added in OpenMOHAA Plus
    void AddText(Event *ev);                   // Added in OpenMOHAA Plus
    void PrintGeometry(int depth) override;    // Added in OpenMOHAA Plus: ui_printwidgets
    //====
    void SetLinkCvarToShader(Event *ev);
    void FrameInitialized() override; // Added in 2.0
    void ProcessSounds();             // Added in 2.0

public:
    UILabel();

    void SetLabel(str lab);
    void Draw(void) override;
    // Added in OpenMOHAA Plus: the text Draw prints (also reported by ui_printwidgets)
    str DisplayText(void);

private:
    str LinkedValue(bool translate);

public:
};
