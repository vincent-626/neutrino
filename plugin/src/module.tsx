import React from 'react';
import { AppPlugin } from '@grafana/data';
import { NeutrinoDrawer } from './components/NeutrinoDrawer';
import type { TimeRange } from '@grafana/data';

interface ExploreToolbarActionContext {
  timeRange: TimeRange;
  datasourceUid?: string;
}

export const plugin = new AppPlugin().configureExtensionLink<ExploreToolbarActionContext>({
  extensionPointId: 'grafana/explore/toolbar/action',
  title: 'Neutrino 🔍',
  description: 'Semantic log search',
  onClick: (_, helpers) => {
    const context = helpers.context;
    if (!context?.datasourceUid) {
      return;
    }

    helpers.openModal({
      title: 'Neutrino — Semantic Log Search',
      body: ({ onDismiss }) => (
        <NeutrinoDrawer
          timeRange={context.timeRange}
          datasourceUid={context.datasourceUid!}
          onDismiss={onDismiss}
        />
      ),
      width: 750,
    });
  },
});
