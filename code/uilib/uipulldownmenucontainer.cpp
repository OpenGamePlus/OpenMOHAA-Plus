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

#include "ui_local.h"

Event EV_UIPulldownMenuContainer_AddPopup
(
    "addpopup",
    EV_DEFAULT,
    "ssss",
    "menuname title type string",
    "Adds a popup to the list box.\n"
    "menuname - the name of the menu to add this to\n"
    "title - the string to display\n"
    "type - type of item this is (command,cvar,event_name)\n"
    "string - the data that corresponds to the correct type\n"
);

Event EV_UIPulldownMenuContainer_MenuShader
(
    "menushader",
    EV_DEFAULT,
    "ss",
    "menuname shader",
    "Adds a menu to the container and sets the shader.\n"
    "menuname - the name of the menu to add this to\n"
    "shader - the string to display"
);

Event EV_UIPulldownMenuContainer_SelectedMenuShader
(
    "selmenushader",
    EV_DEFAULT,
    "ss",
    "menuname shader",
    "Adds a menu to the container and sets the shader when it's selected.\n"
    "menuname - the name of the menu to add this to\n"
    "shader - the string to display"
);

Event EV_UIPulldownMenuContainer_PopupHighlightFGColor
(
    "popup_highlight_fgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the highlight background color of the popup menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_HighlightBGColor
(
    "highlight_bgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the highlight foreground color of the pulldown menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_HighlightFGColor
(
    "highlight_fgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the highlight background color of the pulldown menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_PopupHighlightBGColor
(
    "popup_highlight_bgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the highlight foreground color of the popup menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_PopupFGColor
(
    "popup_fgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the background color of the popup menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_PopupBGColor
(
    "popup_bgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the foreground color of the popup menu\n"
    "menu - the name of the popup menu to color\n"
);

CLASS_DECLARATION(UIWidget, UIPulldownMenuContainer, NULL) {
    {&EV_UIPulldownMenuContainer_AddPopup,              &UIPulldownMenuContainer::AddPopup                },
    {&EV_UIPulldownMenuContainer_MenuShader,            &UIPulldownMenuContainer::SetMenuShader           },
    {&EV_UIPulldownMenuContainer_SelectedMenuShader,    &UIPulldownMenuContainer::SetSelectedMenuShader   },
    {&EV_UIPulldownMenuContainer_PopupHighlightFGColor, &UIPulldownMenuContainer::SetPopupHighlightFGColor},
    {&EV_UIPulldownMenuContainer_PopupHighlightBGColor, &UIPulldownMenuContainer::SetPopupHighlightBGColor},
    {&EV_UIPulldownMenuContainer_PopupFGColor,          &UIPulldownMenuContainer::SetPopupFGColor         },
    {&EV_UIPulldownMenuContainer_PopupBGColor,          &UIPulldownMenuContainer::SetPopupBGColor         },
    {&EV_UIPulldownMenuContainer_HighlightFGColor,      &UIPulldownMenuContainer::SetHighlightFGColor     },
    {&EV_UIPulldownMenuContainer_HighlightBGColor,      &UIPulldownMenuContainer::SetHighlightBGColor     },
    {&EV_Layout_VirtualRes,                             &UIPulldownMenuContainer::PulldownVirtualRes      },
    {NULL,                                              NULL                                              }
};

UIPulldownMenuContainer::UIPulldownMenuContainer()
{
    m_menu = new UIPulldownMenu();
    m_menu->CreateAligned(this, this);
}

UIPulldownMenuContainer::~UIPulldownMenuContainer()
{
    for (int i = m_popups.NumObjects(); i > 0; i--) {
        uipopup_describe *uipd = m_popups.ObjectAt(i);
        m_popups.RemoveObjectAt(i);
        delete uipd;
    }

    for (int i = m_dataContainer.NumObjects(); i > 0; i--) {
        char *data = m_dataContainer.ObjectAt(i);
        m_dataContainer.RemoveObjectAt(i);
        delete data;
    }

    // FIXME: m_menu isn't deleted, possible memory leak!
}

void UIPulldownMenuContainer::FrameInitialized(void)
{
    AllowActivate(qfalse);
    m_menu->setBackgroundColor(m_background_color, qtrue);
    m_menu->setForegroundColor(m_foreground_color);
}

void UIPulldownMenuContainer::setBackgroundAlpha(float f)
{
    m_alpha = f;
    m_menu->setBackgroundAlpha(f);
}

void UIPulldownMenuContainer::setBackgroundColor(const UColor& color, bool setbordercolor)
{
    UIWidget::setBackgroundColor(color, setbordercolor);
    m_menu->setBackgroundColor(color, setbordercolor);
}

void UIPulldownMenuContainer::setForegroundColor(const UColor& color)
{
    UIWidget::setForegroundColor(color);
    m_menu->setForegroundColor(color);
}

void UIPulldownMenuContainer::SetPopupHighlightFGColor(Event *ev)
{
    str   menu = ev->GetString(1);
    float r    = ev->GetFloat(2);
    float g    = ev->GetFloat(3);
    float b    = ev->GetFloat(4);
    float a    = ev->GetFloat(5);

    m_menu->setPopupHighlightFGColor(menu, UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetPopupHighlightBGColor(Event *ev)
{
    str   menu = ev->GetString(1);
    float r    = ev->GetFloat(2);
    float g    = ev->GetFloat(3);
    float b    = ev->GetFloat(4);
    float a    = ev->GetFloat(5);

    m_menu->setPopupHighlightBGColor(menu, UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetPopupFGColor(Event *ev)
{
    str   menu = ev->GetString(1);
    float r    = ev->GetFloat(2);
    float g    = ev->GetFloat(3);
    float b    = ev->GetFloat(4);
    float a    = ev->GetFloat(5);

    m_menu->setPopupFGColor(menu, UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetPopupBGColor(Event *ev)
{
    str   menu = ev->GetString(1);
    float r    = ev->GetFloat(2);
    float g    = ev->GetFloat(3);
    float b    = ev->GetFloat(4);
    float a    = ev->GetFloat(5);

    m_menu->setPopupBGColor(menu, UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetHighlightFGColor(Event *ev)
{
    // original game goes 1-4 for some reason
    float r = ev->GetFloat(2);
    float g = ev->GetFloat(3);
    float b = ev->GetFloat(4);
    float a = ev->GetFloat(5);

    m_menu->setHighlightFGColor(UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetHighlightBGColor(Event *ev)
{
    // original game goes 1-4 for some reason
    float r = ev->GetFloat(2);
    float g = ev->GetFloat(3);
    float b = ev->GetFloat(4);
    float a = ev->GetFloat(5);

    m_menu->setHighlightBGColor(UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetMenuShader(Event *ev)
{
    str               menu   = ev->GetString(1);
    str               shader = ev->GetString(2);
    UIReggedMaterial *mat    = uWinMan.RegisterShader(shader);
    m_menu->setPulldownShader(menu, mat);
}

void UIPulldownMenuContainer::SetSelectedMenuShader(Event *ev)
{
    str               menu   = ev->GetString(1);
    str               shader = ev->GetString(2);
    UIReggedMaterial *mat    = uWinMan.RegisterShader(shader);
    m_menu->setSelectedPulldownShader(menu, mat);
}

void UIPulldownMenuContainer::Realign(void)
{
    UIWidget::Realign();
    m_menu->Realign();
}

void UIPulldownMenuContainer::PulldownVirtualRes(Event *ev)
{
    LayoutVirtualRes(ev);

    if (m_bVirtual) {
        Event *newEv = new Event(EV_Layout_VirtualRes);
        newEv->AddInteger(1);
        m_menu->ProcessEvent(newEv);
    }
}

void UIPulldownMenuContainer::AddPopup(Event *ev)
{
    str menu  = ev->GetString(1);
    str title = ev->GetString(2);
    str t     = ev->GetString(3);
    str d     = ev->GetString(4);

    uipopup_type type = UI_PopupTypeStringToInt(t);

    // Make sure to create a duplicate of the original string,
    // otherwise `data` will point to junk when `d` is destroyed.
    // This only seems to run for each popup menu during game startup,
    // so it doesn't appear to leak memory continuously,
    // but it's being cleaned up in uipopup_describe's dtor anyway.
    void *data = strdup(d);

    uipopup_describe *uipd = new uipopup_describe(title, type, data, NULL);
    m_popups.AddObject(uipd);
    m_menu->AddUIPopupDescribe(menu, uipd);
}

// Added in OpenMOHAA Plus: with a "linkcvar", the title of the popup that sets the cvar to its
//  current (or latched) value: "set|seta <cvar> <value>", or "reset <cvar>" while the cvar is at its default,
//  as the first command of the item; the bare value if no item matches; empty without linkcvar
str UIPulldownMenuContainer::getValueTitle(void) const
{
    if (!m_cvarname.length()) {
        return "";
    }

    const cvar_t *cvar = uii.Cvar_Find(m_cvarname.c_str());
    // a latched cvar (cl_renderer) shows the choice waiting for the restart
    const str value = (cvar && cvar->latchedString) ? cvar->latchedString : uii.Cvar_GetString(m_cvarname.c_str(), "");
    const str     set   = str("set ") + m_cvarname + " " + value;
    const str     seta  = str("seta ") + m_cvarname + " " + value;
    const str     reset = str("reset ") + m_cvarname;

    for (int i = 1; i <= m_popups.NumObjects(); i++) {
        const uipopup_describe *uipd = m_popups.ObjectAt(i);
        if (uipd->type != UIP_CMD && uipd->type != UIP_CVAR) {
            continue;
        }

        char  command[MAX_STRING_CHARS];
        char *end;

        Q_strncpyz(command, (const char *)uipd->data, sizeof(command));
        end = strchr(command, ';');
        if (!end) {
            end = command + strlen(command);
        }
        while (end > command && end[-1] == ' ') {
            end--;
        }
        *end = 0;

        if (!Q_stricmp(command, set) || !Q_stricmp(command, seta)) {
            return uipd->title;
        }
        if (!Q_stricmp(command, reset) && cvar && !strcmp(value.c_str(), cvar->resetString)) {
            return uipd->title;
        }
    }

    return value;
}

// Added in OpenMOHAA Plus: the pulldown shows the current value (see getValueTitle) in this
//  widget's font; the container itself draws nothing, as before
void UIPulldownMenuContainer::Draw(void)
{
    m_menu->setValue(getValueTitle(), m_font);
}

// Added in OpenMOHAA Plus: "ui_printwidgets"; the value is set first so the pulldown (a child)
//  prints what the next frame draws
void UIPulldownMenuContainer::PrintGeometry(int depth)
{
    m_menu->setValue(getValueTitle(), m_font);
    UIWidget::PrintGeometry(depth);
}
